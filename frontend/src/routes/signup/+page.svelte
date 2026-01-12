<script>
	import SignupForm from '$lib/components/signup-form.svelte';
	import ThemeSwitcher from '$lib/components/theme-switcher.svelte';
	import { IsMobile } from '$lib/hooks/is-mobile.svelte.js';

	const isMobile = new IsMobile();
</script>

<div class="relative flex min-h-svh w-full items-center justify-center p-6 md:p-10">
	<div class="absolute top-4 right-4 z-10">
		<ThemeSwitcher />
	</div>
	<div class="w-full max-w-sm" class:mt-16={isMobile.current}>
		<SignupForm />
	</div>
</div>
