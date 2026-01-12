<!-- Ferron-Proxy-Manager/frontend/src/lib/components/hosts-data-table.svelte -->
<script lang="ts">
	import ArrowUpDown from '@lucide/svelte/icons/arrow-up-down';
	import {
		createSvelteTable,
		FlexRender,
		renderComponent,
		renderSnippet
	} from '$lib/components/ui/data-table/index.js';
	import {
		getCoreRowModel,
		getSortedRowModel,
		getFilteredRowModel,
		type ColumnDef,
		type SortingState,
		type ColumnFiltersState
	} from '@tanstack/table-core';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import HostActionButtons from './host-action-buttons.svelte';
	import { createRawSnippet } from 'svelte';
	import LoadBalancerHostForm from './load-balancer-host-form.svelte';
	import ReverseProxyHostForm from './reverse-proxy-host-form.svelte';
	import StaticFileHostForm from './static-file-host-form.svelte';
	import { toast } from 'svelte-sonner';
	import client from '$lib/apiClient';
	import { ApiPaths } from '$lib/api/types';
	import type { components } from '$lib/api/types';
	import { onMount } from 'svelte';

	// Enums and Types
	const HostType = {
		ReverseProxy: 'Reverse Proxy',
		LoadBalancer: 'Load Balancer',
		StaticSite: 'Static Site'
	} as const;

	type HostType = (typeof HostType)[keyof typeof HostType];

	type CreateReverseProxyConfig = components['schemas']['CreateReverseProxyConfig'];
	type CreateLoadBalancerConfig = components['schemas']['CreateLoadBalancerConfig'];
	type CreateStaticFileConfig = components['schemas']['CreateStaticFileConfig'];
	type UpdateReverseProxyConfig = components['schemas']['UpdateReverseProxyConfig'];
	type UpdateLoadBalancerConfig = components['schemas']['UpdateLoadBalancerConfig'];
	type UpdateStaticFileConfig = components['schemas']['UpdateStaticFileConfig'];

	type Host = {
		id: number;
		virtual_host_name: string;
		type: HostType;
		backend_display: string;
		config: UpdateReverseProxyConfig | UpdateLoadBalancerConfig | UpdateStaticFileConfig;
	};

	let data = $state<Host[]>([]);
	let isLoading = $state(true);

	// Table State
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);

	// Edit Dialog State
	let isEditDialogOpen = $state(false);
	let editingHost = $state<Host | null>(null);

	// Fetch all configs on mount
	onMount(async () => {
		await fetchAllConfigs();
	});

	async function fetchAllConfigs() {
		isLoading = true;
		try {
			const [reverseProxyResponse, loadBalancerResponse, staticFileResponse] = await Promise.all([
				client.GET(ApiPaths.read_all_reverse_proxy_config_api_configs_reverse_proxy_all_get),
				client.GET(ApiPaths.read_all_load_balancer_config_api_configs_load_balancer_all_get),
				client.GET(ApiPaths.read_all_static_file_config_api_configs_static_file_all_get)
			]);

			const hosts: Host[] = [];

			// Process reverse proxy configs
			if (reverseProxyResponse.data) {
				reverseProxyResponse.data.forEach((config) => {
					hosts.push({
						id: config.id,
						virtual_host_name: config.virtual_host_name,
						type: HostType.ReverseProxy,
						backend_display: config.backend_url,
						config
					});
				});
			}

			// Process load balancer configs
			if (loadBalancerResponse.data) {
				loadBalancerResponse.data.forEach((config) => {
					hosts.push({
						id: config.id,
						virtual_host_name: config.virtual_host_name,
						type: HostType.LoadBalancer,
						backend_display: config.backend_urls.join(', '),
						config
					});
				});
			}

			// Process static file configs
			if (staticFileResponse.data) {
				staticFileResponse.data.forEach((config) => {
					hosts.push({
						id: config.id,
						virtual_host_name: config.virtual_host_name,
						type: HostType.StaticSite,
						backend_display: config.static_files_dir,
						config
					});
				});
			}

			data = hosts;
		} catch (error) {
			toast.error('Failed to load configurations');
			console.error('Error fetching configs:', error);
		} finally {
			isLoading = false;
		}
	}

	async function handleDelete(host: Host) {
		try {
			let response;

			if (host.type === HostType.ReverseProxy) {
				response = await client.DELETE(
					ApiPaths.delete_reverse_proxy_config_api_configs_reverse_proxy_delete,
					{
						params: {
							query: { reverse_proxy_id: host.id }
						}
					}
				);
			} else if (host.type === HostType.LoadBalancer) {
				response = await client.DELETE(
					ApiPaths.delete_load_balancer_config_api_configs_load_balancer_delete,
					{
						params: {
							query: { load_balancer_id: host.id }
						}
					}
				);
			} else if (host.type === HostType.StaticSite) {
				response = await client.DELETE(
					ApiPaths.delete_static_file_config_api_configs_static_file_delete,
					{
						params: {
							query: { static_file_id: host.id }
						}
					}
				);
			}

			if (response?.response.ok) {
				data = data.filter((h) => h.id !== host.id);
				toast.success(`Host ${host.virtual_host_name} deleted`);
			} else {
				toast.error('Failed to delete host configuration');
			}
		} catch (error) {
			toast.error('Error deleting host configuration');
			console.error('Delete error:', error);
		}
	}

	// Columns Definition
	const columns: ColumnDef<Host>[] = [
		{
			accessorKey: 'virtual_host_name',
			header: 'Host',
			cell: ({ row }) => row.original.virtual_host_name
		},
		{
			accessorKey: 'backend_display',
			header: 'Backend URL(s)',
			cell: ({ row }) => row.original.backend_display
		},
		{
			accessorKey: 'type',
			header: 'Type',
			cell: ({ row }) => {
				const type = row.original.type;
				let badgeClass = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
				if (type === HostType.ReverseProxy)
					badgeClass = 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
				if (type === HostType.LoadBalancer)
					badgeClass = 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
				if (type === HostType.StaticSite)
					badgeClass = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';

				return renderSnippet(
					createRawSnippet(() => ({
						render: () =>
							`<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${badgeClass}">${type}</span>`
					}))
				);
			},
			filterFn: (row, id, value) => {
				return value === 'all' || row.getValue(id) === value;
			}
		},
		{
			id: 'actions',
			header: 'Actions',
			cell: ({ row }) =>
				renderComponent(HostActionButtons, {
					host: row.original,
					onEdit: (host: Host) => {
						editingHost = host;
						isEditDialogOpen = true;
					},
					onDelete: handleDelete
				})
		}
	];

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		state: {
			get sorting() {
				return sorting;
			},
			get columnFilters() {
				return columnFilters;
			}
		},
		onSortingChange: (updater) => {
			if (typeof updater === 'function') {
				sorting = updater(sorting);
			} else {
				sorting = updater;
			}
		},
		onColumnFiltersChange: (updater) => {
			if (typeof updater === 'function') {
				columnFilters = updater(columnFilters);
			} else {
				columnFilters = updater;
			}
		}
	});

	async function handleEditSaveReverseProxy(
		updatedConfig: CreateReverseProxyConfig | UpdateReverseProxyConfig
	) {
		if (!editingHost) return;

		try {
			const response = await client.PATCH(
				ApiPaths.update_reverse_proxy_config_api_configs_reverse_proxy_patch,
				{
					body: updatedConfig as UpdateReverseProxyConfig
				}
			);

			if (response?.response.ok && response.data) {
				const updatedHost: Host = {
					...editingHost,
					config: response.data,
					virtual_host_name: response.data.virtual_host_name,
					backend_display: response.data.backend_url
				};

				const index = data.findIndex((h) => h.id === editingHost!.id);
				if (index !== -1) {
					let newData = [...data];
					newData[index] = updatedHost;
					data = newData;
					toast.success(`Host ${response.data.virtual_host_name} updated`);
				}
				isEditDialogOpen = false;
				editingHost = null;
			} else {
				toast.error('Failed to update host configuration');
			}
		} catch (error) {
			toast.error('Error updating host configuration');
			console.error('Update error:', error);
		}
	}

	async function handleEditSaveLoadBalancer(
		updatedConfig: CreateLoadBalancerConfig | UpdateLoadBalancerConfig
	) {
		if (!editingHost) return;

		try {
			const response = await client.PATCH(
				ApiPaths.update_load_balancer_config_api_configs_load_balancer_patch,
				{
					body: updatedConfig as UpdateLoadBalancerConfig
				}
			);

			if (response?.response.ok && response.data) {
				const updatedHost: Host = {
					...editingHost,
					config: response.data,
					virtual_host_name: response.data.virtual_host_name,
					backend_display: response.data.backend_urls.join(', ')
				};

				const index = data.findIndex((h) => h.id === editingHost!.id);
				if (index !== -1) {
					let newData = [...data];
					newData[index] = updatedHost;
					data = newData;
					toast.success(`Host ${response.data.virtual_host_name} updated`);
				}
				isEditDialogOpen = false;
				editingHost = null;
			} else {
				toast.error('Failed to update host configuration');
			}
		} catch (error) {
			toast.error('Error updating host configuration');
			console.error('Update error:', error);
		}
	}

	async function handleEditSaveStaticFile(
		updatedConfig: CreateStaticFileConfig | UpdateStaticFileConfig
	) {
		if (!editingHost) return;

		try {
			const response = await client.PATCH(
				ApiPaths.update_static_file_config_api_configs_static_file_patch,
				{
					body: updatedConfig as UpdateStaticFileConfig
				}
			);

			if (response?.response.ok && response.data) {
				const updatedHost: Host = {
					...editingHost,
					config: response.data,
					virtual_host_name: response.data.virtual_host_name,
					backend_display: response.data.static_files_dir
				};

				const index = data.findIndex((h) => h.id === editingHost!.id);
				if (index !== -1) {
					let newData = [...data];
					newData[index] = updatedHost;
					data = newData;
					toast.success(`Host ${response.data.virtual_host_name} updated`);
				}
				isEditDialogOpen = false;
				editingHost = null;
			} else {
				toast.error('Failed to update host configuration');
			}
		} catch (error) {
			toast.error('Error updating host configuration');
			console.error('Update error:', error);
		}
	}

	// Export refresh function for parent components
	export function refresh() {
		fetchAllConfigs();
	}
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Input
				placeholder="Filter by hosts..."
				value={(table.getColumn('virtual_host_name')?.getFilterValue() as string) ?? ''}
				oninput={(e) => table.getColumn('virtual_host_name')?.setFilterValue(e.currentTarget.value)}
				class="max-w-sm"
			/>
			<Select.Root
				type="single"
				value={(table.getColumn('type')?.getFilterValue() as string) ?? 'all'}
				onValueChange={(v) => {
					const val = v === 'all' ? undefined : v;
					table.getColumn('type')?.setFilterValue(val as string);
				}}
			>
				<Select.Trigger class="w-45">
					{(table.getColumn('type')?.getFilterValue() as string) || 'Filter by Type'}
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="all">All Types</Select.Item>
					<Select.Item value={HostType.ReverseProxy}>{HostType.ReverseProxy}</Select.Item>
					<Select.Item value={HostType.LoadBalancer}>{HostType.LoadBalancer}</Select.Item>
					<Select.Item value={HostType.StaticSite}>{HostType.StaticSite}</Select.Item>
				</Select.Content>
			</Select.Root>
		</div>
	</div>

	<div class="rounded-md border">
		<Table.Root>
			<Table.Header>
				{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
					<Table.Row>
						{#each headerGroup.headers as header (header.id)}
							<Table.Head class={header.id === 'virtual_host_name' ? 'pl-6' : ''}>
								{#if !header.isPlaceholder}
									{#if header.id === 'virtual_host_name'}
										<Button
											variant="ghost"
											onclick={header.column.getToggleSortingHandler()}
											class="-ml-4"
										>
											Host
											<ArrowUpDown class="ml-2 h-4 w-4" />
										</Button>
									{:else}
										<FlexRender
											content={header.column.columnDef.header}
											context={header.getContext()}
										/>
									{/if}
								{/if}
							</Table.Head>
						{/each}
					</Table.Row>
				{/each}
			</Table.Header>
			<Table.Body>
				{#if isLoading}
					<Table.Row>
						<Table.Cell colspan={columns.length} class="h-24 text-center">
							Loading configurations...
						</Table.Cell>
					</Table.Row>
				{:else}
					{#each table.getRowModel().rows as row (row.id)}
						<Table.Row data-state={row.getIsSelected() && 'selected'}>
							{#each row.getVisibleCells() as cell (cell.id)}
								<Table.Cell class={cell.column.id === 'virtual_host_name' ? 'pl-6' : ''}>
									<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
								</Table.Cell>
							{/each}
						</Table.Row>
					{:else}
						<Table.Row>
							<Table.Cell colspan={columns.length} class="h-24 text-center">No results.</Table.Cell>
						</Table.Row>
					{/each}
				{/if}
			</Table.Body>
		</Table.Root>
	</div>
</div>

<Dialog.Root bind:open={isEditDialogOpen}>
	<Dialog.Content class="max-h-[90vh] max-w-2xl overflow-y-auto">
		{#if editingHost?.type === HostType.LoadBalancer}
			<LoadBalancerHostForm
				initialData={editingHost.config}
				onSubmit={handleEditSaveLoadBalancer}
				onCancel={() => (isEditDialogOpen = false)}
				class="border-0 shadow-none"
			/>
		{:else if editingHost?.type === HostType.ReverseProxy}
			<ReverseProxyHostForm
				initialData={editingHost.config}
				onSubmit={handleEditSaveReverseProxy}
				onCancel={() => (isEditDialogOpen = false)}
				class="border-0 shadow-none"
			/>
		{:else if editingHost?.type === HostType.StaticSite}
			<StaticFileHostForm
				initialData={editingHost.config}
				onSubmit={handleEditSaveStaticFile}
				onCancel={() => (isEditDialogOpen = false)}
				class="border-0 shadow-none"
			/>
		{/if}
	</Dialog.Content>
</Dialog.Root>
