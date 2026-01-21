// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { components } from '$lib/api/types';

declare global {
    namespace App {
        // interface Error {}
        interface Locals {
            user?: components['schemas']['User'];
        }
        // interface PageData {}
        // interface PageState {}
        // interface Platform {}
    }
}

export {};
