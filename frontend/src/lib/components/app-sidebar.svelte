<script lang="ts" module>
    const data = {
        navMain: [
            {
                title: 'Home',
                url: '#',
                items: [
                    {
                        title: 'Server (WIP)',
                        url: '/dashboard'
                    }
                ]
            },
            {
                title: 'Global Configuration',
                url: '#',
                items: [
                    {
                        title: 'Manage Global Configuration',
                        url: '/dashboard/global-config/manage'
                    }
                ]
            },
            {
                title: 'Virtual Hosts',
                url: '#',
                items: [
                    {
                        title: 'Create Virtual Host',
                        url: '/dashboard/hosts/create'
                    },
                    {
                        title: 'Manage Virtual Hosts',
                        url: '/dashboard/hosts/manage'
                    }
                ]
            }
        ]
    };
</script>

<script lang="ts">
    import * as Sidebar from '$lib/components/ui/sidebar/index.js';
    import UpdateNotification from './update-notification.svelte';
    import type { ComponentProps } from 'svelte';
    import { page } from '$app/state';

    let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root {...restProps} bind:ref>
    <Sidebar.Header>
        <div class="pt-3 pl-2 text-lg font-semibold">Ferron Proxy Manager</div>
    </Sidebar.Header>
    <Sidebar.Content>
        {#each data.navMain as group (group.title)}
            <Sidebar.Group>
                <Sidebar.GroupLabel>{group.title}</Sidebar.GroupLabel>
                <Sidebar.GroupContent>
                    <Sidebar.Menu>
                        {#each group.items as item (item.title)}
                            <Sidebar.MenuItem>
                                <Sidebar.MenuButton isActive={page.url.pathname === item.url}>
                                    {#snippet child({ props })}
                                        <a href={item.url} {...props}>{item.title}</a>
                                    {/snippet}
                                </Sidebar.MenuButton>
                            </Sidebar.MenuItem>
                        {/each}
                    </Sidebar.Menu>
                </Sidebar.GroupContent>
            </Sidebar.Group>
        {/each}
    </Sidebar.Content>
    <Sidebar.Footer>
        <UpdateNotification />
    </Sidebar.Footer>
    <Sidebar.Rail />
</Sidebar.Root>
