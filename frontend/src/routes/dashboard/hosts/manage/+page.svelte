<script lang="ts">
	import HostsDataTable from '$lib/components/hosts-data-table.svelte';
</script>

<div class="space-y-6">
	<div>
		<div class="mb-3">
			<h1 class="text-3xl font-bold">Manage Hosts</h1>
		</div>
		<p class="text-sm text-muted-foreground">
			View, edit, and manage your virtual hosts and reverseproxies.
		</p>
	</div>

	<HostsDataTable />
</div>
