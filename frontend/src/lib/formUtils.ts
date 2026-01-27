export type FieldErrors = Record<string, string>;

export interface FormSubmitResult<T> {
    success: boolean;
    data?: T;
    formError?: string;
    fieldErrors?: FieldErrors;
}

export interface ValidationErrorDetail {
    loc: (string | number)[];
    msg: string;
}

export interface ApiErrorDetail {
    error_code?: string;
    msg?: string;
}

export function parseValidationErrors(error: unknown): FieldErrors {
    const fieldErrors: FieldErrors = {};
    const validationError = error as { detail?: ValidationErrorDetail[] };

    if (validationError.detail && Array.isArray(validationError.detail)) {
        validationError.detail.forEach((err) => {
            const fieldName = err.loc[err.loc.length - 1];
            if (typeof fieldName === 'string') {
                fieldErrors[fieldName] = err.msg;
            }
        });
    }

    return fieldErrors;
}

export function parseApiError(error: unknown): string {
    const apiError = error as { detail?: ApiErrorDetail };
    if (apiError.detail?.msg) {
        return apiError.detail.msg;
    }
    return 'An error occurred. Please try again.';
}

export async function handleFormSubmit<TData, TError>(
    apiCall: () => Promise<{
        data?: TData;
        error?: TError;
        response: Response;
    }>,
    options: {
        successStatuses?: number[];
    } = {}
): Promise<FormSubmitResult<TData>> {
    const { successStatuses = [200, 201] } = options;

    try {
        const { data, error, response } = await apiCall();

        if (successStatuses.includes(response.status) && data) {
            return {
                success: true,
                data
            };
        }

        if (response.status === 422 && error) {
            return {
                success: false,
                fieldErrors: parseValidationErrors(error)
            };
        }

        if (error) {
            return {
                success: false,
                formError: parseApiError(error)
            };
        }

        return {
            success: false,
            formError: 'An unexpected error occurred. Please try again.'
        };
    } catch {
        return {
            success: false,
            formError: 'Network error. Please check your connection and try again.'
        };
    }
}
