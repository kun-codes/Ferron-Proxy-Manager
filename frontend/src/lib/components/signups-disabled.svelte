<script>
	import * as Empty from '$lib/components/ui/empty/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { UserX } from '@lucide/svelte';
</script>

<Empty.Root>
	<Empty.Content>
		<Empty.Header>
			<Empty.Media>
				<UserX class="size-12 text-muted-foreground" />
			</Empty.Media>
			<Empty.Title>Sign-ups Disabled</Empty.Title>
			<Empty.Description>
				New user registrations are currently disabled. Please contact your administrator for access.
			</Empty.Description>
		</Empty.Header>
		<Button href="/login" variant="outline">Go to Login</Button>
	</Empty.Content>
</Empty.Root>
