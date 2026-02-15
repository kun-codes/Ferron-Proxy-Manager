<script lang="ts">
    import * as Card from '$lib/components/ui/card';
    import { Button } from '$lib/components/ui/button';
    import client from '$lib/apiClient';
    import { ApiPaths } from '$lib/api/types';
    import type { components } from '$lib/api/types';
    import { onMount } from 'svelte';
    import ExternalLink from '@lucide/svelte/icons/external-link';

    type UpdateAvailableResponse = components['schemas']['UpdateAvailableResponse'];

    let updateInfo = $state<UpdateAvailableResponse | null>(null);
    let isLoading = $state(true);

    async function checkForUpdates() {
        try {
            isLoading = true;

            const { data } = await client.GET(
                ApiPaths.check_update_available_api_management_version_check_get
            );

            if (data && data.update_available) {
                updateInfo = data;
            }
        } catch (err) {
            console.error('Update check error:', err);
        } finally {
            isLoading = false;
        }
    }

    onMount(() => {
        checkForUpdates();
    });
</script>

{#if !isLoading && updateInfo && updateInfo.update_available}
    <Card.Root class="border-primary bg-primary/4">
        <Card.Header class="pb-1">
            <Card.Title class="text-sm font-medium">Update Available</Card.Title>
            <Card.Description class="text-xs">
                A new version of Ferron Proxy Manager is available
            </Card.Description>
        </Card.Header>
        <Card.Content class="pb-1">
            <div class="space-y-1 text-xs">
                <div class="flex items-center justify-between">
                    <span class="text-muted-foreground">Current:</span>
                    <span class="font-medium">{updateInfo.current_version}</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-muted-foreground">Latest:</span>
                    <span class="font-medium">{updateInfo.latest_version}</span>
                </div>
            </div>
        </Card.Content>
        <Card.Footer class="pt-1">
            <Button
                href={updateInfo.release_url}
                target="_blank"
                rel="noopener noreferrer"
                size="sm"
                class="w-full text-xs"
            >
                View Release
                <ExternalLink />
            </Button>
        </Card.Footer>
    </Card.Root>
{/if}
