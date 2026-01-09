<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Field from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import Plus from '@lucide/svelte/icons/plus';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import type { components } from '$lib/api/types';
	import { ApiPaths } from '$lib/api/types';
	import type { ComponentProps } from 'svelte';
	import client from '$lib/apiClient';
	import { toast } from 'svelte-sonner';

	type CreateLoadBalancerConfig = components['schemas']['CreateLoadBalancerConfig'];

	let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

	const initialFormData: CreateLoadBalancerConfig = {
		virtual_host_name: '',
		backend_urls: [''],
		cache: false,
		cache_max_age: 3600,
		preserve_host_header: false,
		lb_health_check: false,
		lb_health_check_max_fails: 3,
		lb_health_check_window: 5000
	};

	let formData = $state<CreateLoadBalancerConfig>({ ...initialFormData });
	let isSubmitting = $state(false);
	let formError = $state('');
	let fieldErrors = $state<Record<string, string>>({});

	const addBackendUrl = () => {
		formData.backend_urls = [...formData.backend_urls, ''];
	};

	const removeBackendUrl = (index: number) => {
		formData.backend_urls = formData.backend_urls.filter((_, i) => i !== index);
	};

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
				ApiPaths.create_load_balancer_config_api_configs_load_balancer_post,
				{
					body: formData
				}
			);

			if (response.status === 200 && data) {
				toast.success('Load balancer configuration created successfully!');
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
		<Card.Title>Load Balancer Configuration</Card.Title>
		<Card.Description>
			Configure a load balancer to distribute traffic across multiple backend servers.
		</Card.Description>
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
						<Field.Description>The hostname for this load balancer configuration.</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label>Backend URLs</Field.Label>
					<div class="space-y-3">
						{#each formData.backend_urls as url, index}
							<div class="flex gap-2">
								<Input
									type="text"
									placeholder="http://localhost:8000"
									bind:value={formData.backend_urls[index]}
									required
									class="flex-1"
									disabled={isSubmitting}
								/>
								<Button
									type="button"
									variant="outline"
									size="icon"
									onclick={() => removeBackendUrl(index)}
									disabled={formData.backend_urls.length === 1 || isSubmitting}
								>
									<Trash2 class="h-4 w-4" />
									<span class="sr-only">Remove URL</span>
								</Button>
							</div>
						{/each}
						<Button type="button" variant="outline" onclick={addBackendUrl} class="w-full" disabled={isSubmitting}>
							<Plus class="mr-2 h-4 w-4" />
							Add Backend URL
						</Button>
					</div>
					{#if fieldErrors.backend_urls}
						<Field.Error>{fieldErrors.backend_urls}</Field.Error>
					{:else}
						<Field.Description>
							The backend server URLs to distribute traffic across.
						</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="cache" bind:checked={formData.cache} disabled={isSubmitting} />
					<Field.Content>
						<Label for="cache" class="font-normal">Enable Caching</Label>
						<Field.Description>
							Cache responses from backend servers to improve performance.
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
							Forward the original Host header to the backend servers.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="lb-health-check" bind:checked={formData.lb_health_check} disabled={isSubmitting} />
					<Field.Content>
						<Label for="lb-health-check" class="font-normal">Enable Health Checks</Label>
						<Field.Description>
							Monitor backend server health and remove unhealthy servers from rotation.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field>
					<Field.Label for="lb-health-check-max-fails">Health Check Max Fails</Field.Label>
					<Input
						id="lb-health-check-max-fails"
						type="number"
						placeholder="3"
						bind:value={formData.lb_health_check_max_fails}
						disabled={!formData.lb_health_check || isSubmitting}
					/>
					{#if fieldErrors.lb_health_check_max_fails}
						<Field.Error>{fieldErrors.lb_health_check_max_fails}</Field.Error>
					{:else}
						<Field.Description>
							Number of consecutive failures before marking a backend as unhealthy.
						</Field.Description>
					{/if}
				</Field.Field>

				<Field.Field>
					<Field.Label for="lb-health-check-window">Health Check Window (milliseconds)</Field.Label>
					<Input
						id="lb-health-check-window"
						type="number"
						placeholder="5000"
						bind:value={formData.lb_health_check_window}
						disabled={!formData.lb_health_check || isSubmitting}
					/>
					{#if fieldErrors.lb_health_check_window}
						<Field.Error>{fieldErrors.lb_health_check_window}</Field.Error>
					{:else}
						<Field.Description>
							Time window in milliseconds for counting health check failures.
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
						{isSubmitting ? 'Creating...' : 'Create Load Balancer'}
					</Button>
					<Field.Description class="px-6 text-center">
						<Button type="button" variant="outline" onclick={cancel} disabled={isSubmitting}>Cancel</Button>
					</Field.Description>
				</Field.Field>
			</Field.Group>
		</form>
	</Card.Content>
</Card.Root>
