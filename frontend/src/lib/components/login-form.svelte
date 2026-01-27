<script lang="ts">
    import { Button } from '$lib/components/ui/button/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import {
        FieldGroup,
        Field,
        FieldLabel,
        FieldDescription,
        FieldError
    } from '$lib/components/ui/field/index.js';
    import client from '$lib/apiClient';
    import { goto } from '$app/navigation';
    import { ApiPaths } from '$lib/api/types';
    import type { components } from '$lib/api/types';
    import { handleFormSubmit, type FieldErrors } from '$lib/formUtils';

    type LoginBody = components['schemas']['Body_login_api_auth_login_post'];

    const id = $props.id();

    let username = $state('');
    let password = $state('');
    let isSubmitting = $state(false);

    let formError = $state('');
    let fieldErrors = $state<FieldErrors>({});

    async function handleSubmit(event: Event) {
        event.preventDefault();

        formError = '';
        fieldErrors = {};
        isSubmitting = true;

        const requestBody: LoginBody = {
            grant_type: 'password',
            username,
            password,
            scope: '',
            client_id: '',
            client_secret: ''
        };

        const result = await handleFormSubmit(() =>
            client.POST(ApiPaths.login_api_auth_login_post, {
                body: requestBody,
                // this converts the typescript object to x-www-form-urlencoded format
                bodySerializer(body) {
                    const formData = new URLSearchParams();
                    for (const [key, value] of Object.entries(body)) {
                        if (value !== null && value !== undefined) {
                            formData.append(key, String(value));
                        }
                    }
                    return formData;
                },
                // TODO: find a way to set this header using the information given in src/lib/api/types.ts
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })
        );

        isSubmitting = false;

        if (result.success) {
            await goto('/dashboard');
        } else {
            formError = result.formError ?? '';
            fieldErrors = result.fieldErrors ?? {};
        }
    }
</script>

<Card.Root class="mx-auto w-full max-w-sm">
    <Card.Header>
        <Card.Title class="text-2xl">Login</Card.Title>
        <Card.Description>Enter your email below to login to your account</Card.Description>
    </Card.Header>
    <Card.Content>
        {#if formError}
            <div
                class="mb-4 rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400"
            >
                {formError}
            </div>
        {/if}

        <form onsubmit={handleSubmit}>
            <FieldGroup>
                <Field>
                    <FieldLabel for="username">Username</FieldLabel>
                    <Input
                        id="username"
                        type="text"
                        placeholder="john_doe"
                        bind:value={username}
                        required
                        disabled={isSubmitting}
                    />
                    {#if fieldErrors.username}
                        <FieldError>{fieldErrors.username}</FieldError>
                    {/if}
                </Field>
                <Field>
                    <div class="flex items-center">
                        <FieldLabel for="password">Password</FieldLabel>
                    </div>
                    <Input
                        id="password"
                        type="password"
                        bind:value={password}
                        required
                        disabled={isSubmitting}
                    />
                    {#if fieldErrors.password}
                        <FieldError>{fieldErrors.password}</FieldError>
                    {/if}
                </Field>
                <Field>
                    <Button type="submit" class="w-full" disabled={isSubmitting}>
                        {isSubmitting ? 'Logging in...' : 'Login'}
                    </Button>
                    <FieldDescription class="text-center">
                        Don't have an account? <a href="/signup">Sign up</a>
                    </FieldDescription>
                </Field>
            </FieldGroup>
        </form>
    </Card.Content>
</Card.Root>
