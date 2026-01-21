import { type Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import { ApiPaths, type components } from '$lib/api/types';
import * as cookie from 'cookie';

if (!env.BACKEND_URL) {
    throw new Error('BACKEND_URL environment variable is not defined');
}

const API_BASE_URL = env.BACKEND_URL;

type User = components['schemas']['User'];

interface AuthCheckResult {
    user: User | null;
    setCookieHeaders: string[];
}

// cookies have to be forwarded since hooks.server.ts runs on the server. This file runs on every request to the
// frontend container. There is no link between the backend and the browser when requests come here. So the cookies
// need to be forwarded to the backend and then handled when backend responds to the frontend with `Set-Cookie`
// headers
async function getAuthenticatedUser(cookieHeader: string): Promise<AuthCheckResult> {
    const result: AuthCheckResult = {
        user: null,
        setCookieHeaders: []
    };

    try {
        const meResponse = await fetch(
            `${API_BASE_URL}${ApiPaths.get_current_user_info_api_auth_me_get}`,
            {
                headers: {
                    Cookie: cookieHeader
                }
            }
        );

        if (meResponse.ok) {
            result.user = (await meResponse.json()) as User;
            return result;
        }

        // 401 is returned when access_token is not found in cookies (due to expiry or invalid token)
        if (meResponse.status === 401) {
            const refreshResponse = await fetch(
                `${API_BASE_URL}${ApiPaths.refresh_token_api_auth_token_refresh_post}`,
                {
                    method: 'POST',
                    headers: {
                        Cookie: cookieHeader
                    }
                }
            );

            if (refreshResponse.status === 200) {
                const setCookieHeaders = refreshResponse.headers.getSetCookie();
                result.setCookieHeaders.push(...setCookieHeaders);

                const existingCookies = cookie.parseCookie(cookieHeader);

                const newCookies: Record<string, string> = {};
                for (const header of setCookieHeaders) {
                    const parsed = cookie.parseCookie(header);
                    Object.assign(newCookies, parsed);
                }

                const mergedCookies = { ...existingCookies, ...newCookies };

                const updatedCookieHeader = cookie.stringifyCookie(mergedCookies);

                const retryMeResponse = await fetch(
                    `${API_BASE_URL}${ApiPaths.get_current_user_info_api_auth_me_get}`,
                    {
                        headers: {
                            Cookie: updatedCookieHeader
                        }
                    }
                );

                if (retryMeResponse.ok) {
                    result.user = (await retryMeResponse.json()) as User;
                }
            }
        }

        return result;
    } catch (error) {
        console.error('Error checking authentication:', error);
        return result;
    }
}

export const handle: Handle = async ({ event, resolve }) => {
    const cookieHeader = event.request.headers.get('cookie') || '';

    const { user, setCookieHeaders } = await getAuthenticatedUser(cookieHeader);

    if (user) {
        event.locals.user = user;
    }

    const path = event.url.pathname;

    let redirectTo: string | null = null;

    // only logged in users can access paths starting with /dashboard
    if (path.startsWith('/dashboard') && !user) {
        redirectTo = '/login';
    }

    // redirect logged in users away from login/signup pages
    if (user && (path === '/login' || path === '/signup')) {
        redirectTo = '/dashboard';
    }

    if (path === '/') {
        if (user) {
            redirectTo = '/dashboard';
        } else {
            redirectTo = '/login';
        }
    }

    // create a redirect response if redirecting, response is being created instead of throwing a redirect because
    // throwing a redirect will not allow us to execute code written after the throw redirect()
    const response = redirectTo
        ? new Response(null, { status: 303, headers: { location: redirectTo } })
        : await resolve(event);

    if (setCookieHeaders.length > 0) {
        for (const setCookie of setCookieHeaders) {
            response.headers.append('set-cookie', setCookie);
        }
    }

    return response;
};
