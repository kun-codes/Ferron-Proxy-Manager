<script lang="ts">
    import { Globe } from '@lucide/svelte';
    import type { HTMLAttributes } from 'svelte/elements';
    import { cn, type WithElementRef } from '$lib/utils.js';

    type DashboardHost = {
        virtual_host_name: string;
        target_url: string;
        favicon_data_url: string;
        is_placeholder: boolean;
    };

    let {
        ref = $bindable(null),
        class: className,
        host,
        ...restProps
    }: WithElementRef<HTMLAttributes<HTMLAnchorElement>> & { host: DashboardHost } = $props();
</script>

<a
    bind:this={ref}
    href={host.target_url}
    target="_blank"
    rel="noopener noreferrer"
    data-slot="dashboard-host-card"
    class={cn(
        'flex flex-col items-center justify-center gap-3 rounded-xl border bg-card p-6 text-card-foreground shadow-sm transition-all hover:border-primary/30 hover:shadow-md',
        className
    )}
    {...restProps}
>
    {#if host.favicon_data_url}
        <img
            src={host.favicon_data_url}
            alt={`${host.virtual_host_name} favicon`}
            class="size-12 object-contain"
        />
    {:else}
        <Globe class="size-12 text-muted-foreground" />
    {/if}
    <span class="max-w-full truncate text-center text-sm leading-tight font-medium">
        {host.virtual_host_name}
    </span>
</a>
