<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Field from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import type { components } from '$lib/api/types';
	import type { ComponentProps } from 'svelte';

	type CreateStaticFileConfig = components['schemas']['CreateStaticFileConfig'];

	let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

	const initialFormData: CreateStaticFileConfig = {
		virtual_host_name: '',
		static_files_dir: '',
		cache: false,
		cache_max_age: 3600,
		use_spa: false,
		compressed: true,
		directory_listing: false,
		precompressed: false
	};

	let formData = $state<CreateStaticFileConfig>({ ...initialFormData });

	const cancel = () => {
		formData = { ...initialFormData };
	};
</script>

<Card.Root {...restProps}>
	<Card.Header>
		<Card.Title>Static File Configuration</Card.Title>
		<Card.Description>
			Configure a static file server to serve files from a directory.
		</Card.Description>
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
					<Field.Description>The hostname for this static file server.</Field.Description>
				</Field.Field>

				<Field.Field>
					<Field.Label for="static-files-dir">Static Files Directory</Field.Label>
					<Input
						id="static-files-dir"
						type="text"
						placeholder="/var/www/html"
						bind:value={formData.static_files_dir}
						required
					/>
					<Field.Description>
						The directory path where static files are located.
					</Field.Description>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="cache" bind:checked={formData.cache} />
					<Field.Content>
						<Label for="cache" class="font-normal">Enable Caching</Label>
						<Field.Description>
							Cache static files to improve performance.
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
						How long cached files should be stored (in seconds).
					</Field.Description>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="use-spa" bind:checked={formData.use_spa} />
					<Field.Content>
						<Label for="use-spa" class="font-normal">Single Page Application Mode</Label>
						<Field.Description>
							Serve index.html for all routes (useful for SPAs like React, Vue, etc.).
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="compressed" bind:checked={formData.compressed} />
					<Field.Content>
						<Label for="compressed" class="font-normal">Enable Compression</Label>
						<Field.Description>
							Compress files on-the-fly using gzip or brotli.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="directory-listing" bind:checked={formData.directory_listing} />
					<Field.Content>
						<Label for="directory-listing" class="font-normal">Directory Listing</Label>
						<Field.Description>
							Show directory contents when accessing a directory URL.
						</Field.Description>
					</Field.Content>
				</Field.Field>

				<Field.Field orientation="horizontal">
					<Checkbox id="precompressed" bind:checked={formData.precompressed} />
					<Field.Content>
						<Label for="precompressed" class="font-normal">Precompressed Files</Label>
						<Field.Description>
							Serve pre-compressed files.
						</Field.Description>
					</Field.Content>
				</Field.Field>
			</Field.Group>

			<Field.Group>
				<Field.Field>
					<Button type="submit">Create Static File Server</Button>
					<Field.Description class="px-6 text-center">
						<Button type="button" variant="outline" onclick={cancel}>Cancel</Button>
					</Field.Description>
				</Field.Field>
			</Field.Group>
		</form>
	</Card.Content>
</Card.Root>
