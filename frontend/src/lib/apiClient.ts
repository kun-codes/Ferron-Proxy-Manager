import createClient, {type Middleware} from 'openapi-fetch';
import type {paths} from './api/types';
import {ApiPaths} from './api/types';
import {goto} from '$app/navigation';

const UNPROTECTED_ROUTES = [
    ApiPaths.signup_api_auth_signup_post,
    ApiPaths.login_api_auth_login_post
];

interface ApiErrorDetail {
    error_code: string;
    msg: string;
}

interface ApiErrorResponse {
    detail: ApiErrorDetail;
}

function isInvalidTokenError(errorBody: unknown): boolean {
    if (typeof errorBody === 'object' && errorBody !== null && 'detail' in errorBody) {
        const detail = (errorBody as ApiErrorResponse).detail;
        return (
            typeof detail === 'object' && detail !== null && detail.error_code === 'invalid_token'
        );
    }
    return false;
}

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;
const requestClones = new WeakMap<Request, Request>();

// base url is blank because all requests are proxied through the sveltekit server to the fastapi backend
const client = createClient<paths>({
    baseUrl: '',
    credentials: 'include'
});

async function refreshAccessToken(): Promise<boolean> {
    // if a refresh is already happening, lets wait for it to complete
    if (isRefreshing && refreshPromise) {
        return refreshPromise;
    }

    isRefreshing = true;

    refreshPromise = (async () => {
        try {
            const {response} = await client.POST(
                ApiPaths.refresh_token_api_auth_token_refresh_post
            );

            if (response.ok) {
                return true;
            }

            return false;
        } catch {
            return false;
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();

    return refreshPromise;
}

function redirectToLogin(): void {
    goto('/login');
}

async function retryRequest(request: Request): Promise<Response> {
    const cloneSource = requestClones.get(request) || request;
    const clonedRequest = cloneSource.clone();
    return fetch(clonedRequest, {
        credentials: 'include'
    });
}

const authMiddleware: Middleware = {
    async onRequest({request, schemaPath}) {
        if (UNPROTECTED_ROUTES.some((pathname) => schemaPath.startsWith(pathname))) {
            return undefined;
        }

        try {
            requestClones.set(request, request.clone());
        } catch {
            // ignoring errors
        }

        return undefined;
    },
    async onResponse({request, response}) {
        if (response.status !== 401) {
            return response;
        }

        // skip token refresh for the refresh endpoint itself to prevent loops
        if (request.url.includes(ApiPaths.refresh_token_api_auth_token_refresh_post)) {
            return response;
        }

        const clonedResponse = response.clone();

        try {
            const errorBody = await clonedResponse.json();

            if (!isInvalidTokenError(errorBody)) {
                return response;
            }

            const refreshSuccessful = await refreshAccessToken();

            if (refreshSuccessful) {
                const retryResponse = await retryRequest(request);
                return retryResponse;
            } else {
                redirectToLogin();
                return response;
            }
        } catch {
            return response;
        }
    }
};

client.use(authMiddleware);

export default client;
