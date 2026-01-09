<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Field from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import type { components } from '$lib/api/types';
    import type { ComponentProps } from 'svelte';

	type CreateReverseProxyConfig = components['schemas']['CreateReverseProxyConfig'];

	let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

	const initialFormData: CreateReverseProxyConfig = {
		virtual_host_name: '',
		backend_url: '',
		cache: false,
		cache_max_age: 3600,
		preserve_host_header: false,
		use_unix_socket: false,
		unix_socket_path: undefined
	};

	let formData = $state<CreateReverseProxyConfig>({ ...initialFormData });

	const cancel = () => {
		formData = { ...initialFormData };
	};
</script>

<Card.Root {...restProps}>
	<Card.Header>
		<Card.Title>Reverse Proxy Configuration</Card.Title>
		<Card.Description>Configure a reverse proxy host to route requests to a backend server.</Card.Description>
	</Card.Header>
	<Card.Content>
		<form class="space-y-6">
			<Field.Group>
				<Field.Field>
					<Field.Label for="virtual-host-name">Virtual Host Name</Field.Label>
					<Input
						id="virtual-host-name"
						type="text"
						placeholder="example.com"
						bind:value={formData.virtual_host_name}
						required
					/>
					<Field.Description>The hostname for this reverse proxy configuration.</Field.Description>
				</Field.Field>

				<Field.Field>
					<Field.Label for="backend-url">Backend URL</Field.Label>
					<Input
						id="backend-url"
						type="text"
						placeholder="http://localhost:8000"
						bind:value={formData.backend_url}
						required
					/>
					<Field.Description>The backend server URL to proxy requests to.</Field.Description>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="cache" bind:checked={formData.cache} />
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
						disabled={!formData.cache}
					/>
					<Field.Description>
						How long cached responses should be stored (in seconds).
					</Field.Description>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="preserve-host-header" bind:checked={formData.preserve_host_header} />
					<Field.Content>
						<Label for="preserve-host-header" class="font-normal">Preserve Host Header</Label>
						<Field.Description>
							Forward the original Host header to the backend server.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="use-unix-socket" bind:checked={formData.use_unix_socket} />
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
						disabled={!formData.use_unix_socket}
					/>
					<Field.Description>
						Path to the Unix socket for backend connection (when using Unix socket).
					</Field.Description>
				</Field.Field>
			</Field.Group>

			<Field.Group>
				<Field.Field>
					<Button type="submit">Create Reverse Proxy</Button>
					<Field.Description class="px-6 text-center">
						<Button type="button" variant="outline" onclick={cancel}>Cancel</Button>
					</Field.Description>
				</Field.Field>
			</Field.Group>
		</form>
	</Card.Content>
</Card.Root>
