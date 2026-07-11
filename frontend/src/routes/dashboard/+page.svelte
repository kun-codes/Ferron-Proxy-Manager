<script lang="ts">
    import { onDestroy, onMount } from 'svelte';
    import client from '$lib/apiClient';
    import { ApiPaths, type components } from '$lib/api/types';
    import DashboardHostCard from '$lib/components/dashboard-host-card.svelte';
    import { AlertCircle, Globe } from '@lucide/svelte';
    import * as Card from '$lib/components/ui/card/index.js';
    import * as Empty from '$lib/components/ui/empty/index.js';
    import { Skeleton } from '$lib/components/ui/skeleton/index.js';

    type DashboardHost = components['schemas']['DashboardHost'];

    const POLL_INTERVAL_MS = 2000;

    let hosts: DashboardHost[] = $state([]);
    let loadError = $state(false);
    let loading = $state(true);
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    onMount(async () => {
        const { data, error } = await client.GET(ApiPaths.read_dashboard_hosts_api_fpm_dashboard_get);

        if (error) {
            loadError = true;
        } else {
            hosts = data ?? [];
            startPolling();
        }
        loading = false;
    });

    onDestroy(() => {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
    });

    function startPolling() {
        if (!hosts.some((h) => h.is_placeholder)) {
            return;
        }

        pollInterval = setInterval(async () => {
            const placeholders = hosts.filter((h) => h.is_placeholder);

            if (placeholders.length === 0) {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
                return;
            }

            for (const host of placeholders) {
                const { data } = await client.GET(
                    ApiPaths.read_host_favicon_api_fpm_dashboard__virtual_host_name__favicon_get,
                    { params: { path: { virtual_host_name: host.virtual_host_name } } },
                );

                if (data) {
                    const index = hosts.findIndex((h) => h.virtual_host_name === host.virtual_host_name);
                    if (index !== -1) {
                        hosts[index] = { ...hosts[index], ...data };
                    }
                }
            }
        }, POLL_INTERVAL_MS);
    }
</script>

{#if loading}
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {#each Array(12) as _}
            <div
                class="flex flex-col items-center justify-center gap-3 rounded-xl border bg-card p-6 text-card-foreground shadow-sm"
            >
                <Skeleton class="size-12 rounded-full" />
                <Skeleton class="h-4 w-24" />
            </div>
        {/each}
    </div>
{:else if loadError}
    <Empty.Root class="min-h-[50vh]">
        <Empty.Content>
            <Empty.Header>
                <Empty.Media>
                    <AlertCircle class="size-12 text-destructive" />
                </Empty.Media>
                <Empty.Title>Failed to load dashboard</Empty.Title>
                <Empty.Description>
                    Could not fetch dashboard data. Please try again later.
                </Empty.Description>
            </Empty.Header>
        </Empty.Content>
    </Empty.Root>
{:else if hosts.length === 0}
    <Empty.Root class="min-h-[50vh]">
        <Empty.Content>
            <Empty.Header>
                <Empty.Media>
                    <Globe class="size-12 text-muted-foreground" />
                </Empty.Media>
                <Empty.Title>No hosts configured</Empty.Title>
                <Empty.Description>
                    Create a virtual host to see it here on the dashboard.
                </Empty.Description>
            </Empty.Header>
        </Empty.Content>
    </Empty.Root>
{:else}
    <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {#each hosts as host (host.virtual_host_name)}
            <DashboardHostCard {host} />
        {/each}
    </div>
{/if}
