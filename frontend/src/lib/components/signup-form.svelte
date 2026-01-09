<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Field from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import type { ComponentProps } from 'svelte';
	import client from '$lib/apiClient';
	import { goto } from '$app/navigation';
	import { ApiPaths } from '$lib/api/types';
	import type { components } from '$lib/api/types';

	type UserCreate = components['schemas']['UserCreate'];

	let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let isSubmitting = $state(false);

	let formError = $state('');
	let fieldErrors = $state<Record<string, string>>({});

	async function handleSubmit(event: Event) {
		event.preventDefault();

		// on submission clear all errors
		formError = '';
		fieldErrors = {};

		// client side check for password match
		if (password !== confirmPassword) {
			fieldErrors.confirm_password = 'Passwords do not match';
			return;
		}

		isSubmitting = true;

		try {
			const requestBody: UserCreate = {
				username,
				email,
				password
			};

			const { data, error, response } = await client.POST(ApiPaths.signup_api_auth_signup_post, {
				body: requestBody
			});

			if (response.status === 201 && data) {
				await goto('/login');
			} else if (response.status === 422 && error) {
				const validationError = error as { detail?: Array<{ loc: (string | number)[]; msg: string }> };
				if (validationError.detail) {
					validationError.detail.forEach((err) => {
						const fieldName = err.loc[err.loc.length - 1];
						if (typeof fieldName === 'string') {
							fieldErrors[fieldName] = err.msg;
						}
					});
				}
			} else if (error) {
				const apiError = error as { detail?: { error_code?: string; msg?: string } };
				if (apiError.detail?.msg) {
					formError = apiError.detail.msg;
				} else {
					formError = 'An error occurred. Please try again.';
				}
			} else {
				formError = 'An unexpected error occurred. Please try again.';
			}
		} catch (err) {
			formError = 'Network error. Please check your connection and try again.';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Card.Root {...restProps}>
	<Card.Header>
		<Card.Title>Create an account</Card.Title>
		<Card.Description>Enter your information below to create your account</Card.Description>
	</Card.Header>
	<Card.Content>
		{#if formError}
			<div class="mb-4 rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
				{formError}
			</div>
		{/if}

		<form onsubmit={handleSubmit}>
			<Field.Group>
				<Field.Field>
					<Field.Label for="username">Username</Field.Label>
					<Input
						id="username"
						type="text"
						placeholder="john_doe"
						bind:value={username}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.username}
						<Field.Error>{fieldErrors.username}</Field.Error>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label for="email">Email</Field.Label>
					<Input
						id="email"
						type="email"
						placeholder="me@example.com"
						bind:value={email}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.email}
						<Field.Error>{fieldErrors.email}</Field.Error>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label for="password">Password</Field.Label>
					<Input
						id="password"
						type="password"
						bind:value={password}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.password}
						<Field.Error>{fieldErrors.password}</Field.Error>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label for="confirm-password">Confirm Password</Field.Label>
					<Input
						id="confirm-password"
						type="password"
						bind:value={confirmPassword}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.confirm_password}
						<Field.Error>{fieldErrors.confirm_password}</Field.Error>
					{:else}
						<Field.Description>Please confirm your password.</Field.Description>
					{/if}
				</Field.Field>

				<Field.Group>
					<Field.Field>
						<Button type="submit" disabled={isSubmitting}>
							{isSubmitting ? 'Creating Account...' : 'Create Account'}
						</Button>
						<Field.Description class="px-6 text-center">
							Already have an account? <a href="/login">Sign in</a>
						</Field.Description>
					</Field.Field>
				</Field.Group>
			</Field.Group>
		</form>
	</Card.Content>
</Card.Root>
