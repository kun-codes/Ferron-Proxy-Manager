<script lang="ts">
	import ReverseProxyHostForm from '$lib/components/reverse-proxy-host-form.svelte';
	import LoadBalancerHostForm from '$lib/components/load-balancer-host-form.svelte';
	import StaticFileHostForm from '$lib/components/static-file-host-form.svelte';
	import ConfigTypeSelector from '$lib/components/config-type-selector.svelte';
	import FileText from '@lucide/svelte/icons/file-text';

	type ConfigType = 'reverse-proxy' | 'load-balancer' | 'static-file';

	let selectedType = $state<ConfigType>('reverse-proxy');
</script>

<div class="mb-6">
	<h1 class="text-3xl font-bold">Create New Configuration</h1>
</div>

<div class="grid gap-6 lg:grid-cols-[400px_1fr] items-start">
	<div >
		<ConfigTypeSelector selected={selectedType} onselect={(type) => (selectedType = type)} />
	</div>

	<div>
		<div class="mb-4">
			<h2 class="flex items-center gap-2 text-sm font-medium">
				<FileText class="h-4 w-4" />
				Configuration Details
			</h2>
		</div>

		{#if selectedType === 'reverse-proxy'}
			<ReverseProxyHostForm />
		{:else if selectedType === 'load-balancer'}
			<LoadBalancerHostForm />
		{:else if selectedType === 'static-file'}
			<StaticFileHostForm />
		{/if}
	</div>
</div>
