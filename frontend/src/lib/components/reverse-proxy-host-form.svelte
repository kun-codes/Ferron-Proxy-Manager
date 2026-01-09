<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Field from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import type { components } from '$lib/api/types';
	import { ApiPaths } from '$lib/api/types';
	import type { ComponentProps } from 'svelte';
	import client from '$lib/apiClient';
	import { toast } from 'svelte-sonner';

	type CreateReverseProxyConfig = components['schemas']['CreateReverseProxyConfig'];

	let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

	const initialFormData: CreateReverseProxyConfig = {
		virtual_host_name: '',
		backend_url: '',
		cache: false,
		cache_max_age: 3600,
		preserve_host_header: false,
		use_unix_socket: false,
		unix_socket_path: ""
	};

	let formData = $state<CreateReverseProxyConfig>({ ...initialFormData });
	let isSubmitting = $state(false);
	let formError = $state('');
	let fieldErrors = $state<Record<string, string>>({});

	const cancel = () => {
		formData = { ...initialFormData };
		formError = '';
		fieldErrors = {};
	};

	async function handleSubmit(event: Event) {
		event.preventDefault();

		// Clear all errors on submission
		formError = '';
		fieldErrors = {};

		isSubmitting = true;

		try {
			const { data, error, response } = await client.POST(
				ApiPaths.create_reverse_proxy_config_api_configs_reverse_proxy_post,
				{
					body: formData
				}
			);

			if (response.status === 200 && data) {
				toast.success('Reverse proxy configuration created successfully!');
				formData = { ...initialFormData };
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
		<Card.Title>Reverse Proxy Configuration</Card.Title>
		<Card.Description>Configure a reverse proxy host to route requests to a backend server.</Card.Description>
	</Card.Header>
	<Card.Content>
		{#if formError}
			<div class="mb-4 rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
				{formError}
			</div>
		{/if}

		<form onsubmit={handleSubmit} class="space-y-6">
			<Field.Group>
				<Field.Field>
					<Field.Label for="virtual-host-name">Virtual Host Name</Field.Label>
					<Input
						id="virtual-host-name"
						type="text"
						placeholder="example.com"
						bind:value={formData.virtual_host_name}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.virtual_host_name}
						<Field.Error>{fieldErrors.virtual_host_name}</Field.Error>
					{:else}
						<Field.Description>The hostname for this reverse proxy configuration.</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label for="backend-url">Backend URL</Field.Label>
					<Input
						id="backend-url"
						type="text"
						placeholder="http://localhost:8000"
						bind:value={formData.backend_url}
						required
						disabled={isSubmitting}
					/>
					{#if fieldErrors.backend_url}
						<Field.Error>{fieldErrors.backend_url}</Field.Error>
					{:else}
						<Field.Description>The backend server URL to proxy requests to.</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="cache" bind:checked={formData.cache} disabled={isSubmitting} />
					<Field.Content>
						<Label for="cache" class="font-normal">Enable Caching</Label>
						<Field.Description>
							Cache responses from the backend server to improve performance.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field>
					<Field.Label for="cache-max-age">Cache Max Age (seconds)</Field.Label>
					<Input
						id="cache-max-age"
						type="number"
						placeholder="3600"
						bind:value={formData.cache_max_age}
						disabled={!formData.cache || isSubmitting}
					/>
					{#if fieldErrors.cache_max_age}
						<Field.Error>{fieldErrors.cache_max_age}</Field.Error>
					{:else}
						<Field.Description>
							How long cached responses should be stored (in seconds).
						</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="preserve-host-header" bind:checked={formData.preserve_host_header} disabled={isSubmitting} />
					<Field.Content>
						<Label for="preserve-host-header" class="font-normal">Preserve Host Header</Label>
						<Field.Description>
							Forward the original Host header to the backend server.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="use-unix-socket" bind:checked={formData.use_unix_socket} disabled={isSubmitting} />
					<Field.Content>
						<Label for="use-unix-socket" class="font-normal">Use Unix Socket</Label>
						<Field.Description>
							Connect to the backend via a Unix socket instead of HTTP.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field>
					<Field.Label for="unix-socket-path">Unix Socket Path</Field.Label>
					<Input
						id="unix-socket-path"
						type="text"
						placeholder="/tmp/backend.sock"
						bind:value={formData.unix_socket_path}
						disabled={!formData.use_unix_socket || isSubmitting}
					/>
					{#if fieldErrors.unix_socket_path}
						<Field.Error>{fieldErrors.unix_socket_path}</Field.Error>
					{:else}
						<Field.Description>
							Path to the Unix socket for backend connection (when using Unix socket).
						</Field.Description>
					{/if}
				</Field.Field>
			</Field.Group>

			{#if formError}
				<div class="rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400">
					{formError}
				</div>
			{/if}

			<Field.Group>
				<Field.Field>
					<Button type="submit" disabled={isSubmitting}>
						{isSubmitting ? 'Creating...' : 'Create Reverse Proxy'}
					</Button>
					<Field.Description class="px-6 text-center">
						<Button type="button" variant="outline" onclick={cancel} disabled={isSubmitting}>Cancel</Button>
					</Field.Description>
				</Field.Field>
			</Field.Group>
		</form>
	</Card.Content>
</Card.Root>
