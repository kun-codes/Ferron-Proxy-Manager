<script>
	import { page } from '$app/state';
	import Error404 from '$lib/components/error-404.svelte';
</script>

<div class="flex min-h-screen items-center justify-center">
	{#if page.status === 404}
		<Error404 />
	{/if}
</div>
