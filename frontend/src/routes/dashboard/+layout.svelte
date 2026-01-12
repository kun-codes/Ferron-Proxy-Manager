<script lang="ts">
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import UserDropdown from '$lib/components/user-dropdown.svelte';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
</script>

<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<header class="flex h-16 shrink-0 items-center gap-2 border-b px-4">
			<Sidebar.Trigger class="-ms-1" />
			<Separator orientation="vertical" class="me-2 h-4" />
			<UserDropdown class="ml-auto" />
		</header>
		<div class="flex flex-1 flex-col gap-4 p-4">
			<slot />
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>
