import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './api/types';
import { ApiPaths } from './api/types';
import { goto } from '$app/navigation';

const UNPROTECTED_ROUTES = [
	ApiPaths.signup_api_auth_signup_post,
	ApiPaths.login_api_auth_login_post
];

// Error response structure from the API
interface ApiErrorDetail {
	error_code: string;
	msg: string;
}

interface ApiErrorResponse {
	detail: ApiErrorDetail;
}

// Check if the error response indicates an invalid token
function isInvalidTokenError(errorBody: unknown): boolean {
	if (typeof errorBody === 'object' && errorBody !== null && 'detail' in errorBody) {
		const detail = (errorBody as ApiErrorResponse).detail;
		return typeof detail === 'object' && detail !== null && detail.error_code === 'invalid_token';
	}
	return false;
}

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;
// store request clones for retrying (associating original request with a fresh clone)
const requestClones = new WeakMap<Request, Request>();

const client = createClient<paths>({
	baseUrl: 'http://localhost:8000',
	credentials: 'include'
});

/**
 * Attempt to refresh the access token
 * Returns true if refresh was successful, false otherwise
 */
async function refreshAccessToken(): Promise<boolean> {
	// If already refreshing, wait for that attempt to complete
	if (isRefreshing && refreshPromise) {
		return refreshPromise;
	}

	isRefreshing = true;

	refreshPromise = (async () => {
		try {
			const { response } = await client.POST(ApiPaths.refresh_token_api_auth_token_refresh_post);

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
	// use the stored clone if available (because the original body might be consumed)
	const cloneSource = requestClones.get(request) || request;
	const clonedRequest = cloneSource.clone();
	return fetch(clonedRequest, {
		credentials: 'include'
	});
}

const authMiddleware: Middleware = {
	async onRequest({ request, schemaPath }) {
		// Skip auth for unprotected routes
		if (UNPROTECTED_ROUTES.some((pathname) => schemaPath.startsWith(pathname))) {
			return undefined;
		}

		// store a clone of the request for potential retry
		try {
			requestClones.set(request, request.clone());
		} catch {
			// ignoring errors
		}

		return undefined;
	},
	async onResponse({ request, response }) {
		if (response.status !== 401) {
			return response;
		}

		// skip token refresh for the refresh endpoint itself to prevent loops
		if (request.url.includes(ApiPaths.refresh_token_api_auth_token_refresh_post)) {
			return response;
		}

		// clone response to read the body (since body can only be read once)
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
