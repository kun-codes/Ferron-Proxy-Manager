<script lang="ts">
    import LoginForm from '$lib/components/login-form.svelte';
    import ThemeSwitcher from '$lib/components/theme-switcher.svelte';
    import { IsMobile } from '$lib/hooks/is-mobile.svelte.js';

    const isMobile = new IsMobile();
</script>

<div class="relative flex h-screen w-full items-center justify-center px-4">
    <div class="absolute top-4 right-4 z-10">
        <ThemeSwitcher />
    </div>
    <div class="w-full max-w-sm" class:mt-16={isMobile.current}>
        <LoginForm />
    </div>
</div>
