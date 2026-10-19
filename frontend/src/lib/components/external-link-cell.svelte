<script lang="ts">
    import ExternalLink from '@lucide/svelte/icons/external-link';

    let { href, label }: { href: string; label: string } = $props();
</script>

<a
    {href}
    target="_blank"
    rel="noopener noreferrer"
    class="inline-flex max-w-full items-center gap-1.5 text-link hover:underline"
>
    <span class="truncate">{label}</span>
    <ExternalLink class="h-3.5 w-3.5 shrink-0" />
</a>
