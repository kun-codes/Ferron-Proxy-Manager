<script lang="ts">
    import { ConstructionIcon } from '@lucide/svelte';
    import * as Empty from '$lib/components/ui/empty/index.js';
</script>

<Empty.Root class="min-h-[50vh]">
    <Empty.Content>
        <Empty.Header>
            <Empty.Media>
                <ConstructionIcon class="size-12 text-muted-foreground" />
            </Empty.Media>
            <Empty.Title>Dashboard is a Work in Progress</Empty.Title>
            <Empty.Description>
                This route is currently under construction. It will be added in a future update.
            </Empty.Description>
        </Empty.Header>
    </Empty.Content>
</Empty.Root>
