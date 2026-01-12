<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import User from '@lucide/svelte/icons/user';
	import LogOut from '@lucide/svelte/icons/log-out';
	import client from '$lib/apiClient.js';
	import { ApiPaths } from '$lib/api/types.js';
	import { goto } from '$app/navigation';
	import type { components } from '$lib/api/types.js';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	type UserType = components['schemas']['User'];

	let {
		class: className = '',
		...restProps
	}: {
		class?: string;
	} = $props();

	let currentUser = $state<UserType | null>(null);
	let isLoading = $state(true);

	async function fetchCurrentUser() {
		try {
			const { data, response } = await client.GET(ApiPaths.get_current_user_info_api_auth_me_get);

			if (response.ok && data) {
				currentUser = data;
			} else {
				console.error('Failed to fetch current user');
			}
		} catch (error) {
			console.error('Error fetching current user:', error);
		} finally {
			isLoading = false;
		}
	}

	async function handleLogout() {
		try {
			const { response } = await client.POST(ApiPaths.logout_api_auth_logout_post);

			if (response.ok) {
				// Show success toast and redirect to login page
				toast.success('Logged out successfully');
				goto('/login');
			} else {
				console.error('Logout failed');
				toast.error('Failed to logout. Please try again.');
			}
		} catch (error) {
			console.error('Error during logout:', error);
			toast.error('An error occurred during logout. Please try again.');
		}
	}

	onMount(() => {
		fetchCurrentUser();
	});
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger class={className}>
		<Button variant="outline" class="gap-2">
			{#if isLoading}
				<User class="size-4" />
				<span>Loading...</span>
			{:else if currentUser}
				<User class="size-4" />
				<span>{currentUser.username}</span>
			{/if}
		</Button>
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end">
		<DropdownMenu.Item onclick={handleLogout}>
			<LogOut class="size-4" />
			Logout
		</DropdownMenu.Item>
	</DropdownMenu.Content>
</DropdownMenu.Root>
