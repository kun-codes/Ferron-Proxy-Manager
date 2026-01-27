<script lang="ts">
    import { Button } from '$lib/components/ui/button/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import { Checkbox } from '$lib/components/ui/checkbox/index.js';
    import * as Field from '$lib/components/ui/field/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Label } from '$lib/components/ui/label/index.js';
    import type { components } from '$lib/api/types';
    import { ApiPaths } from '$lib/api/types';
    import { type ComponentProps } from 'svelte';
    import client from '$lib/apiClient';
    import { toast } from 'svelte-sonner';
    import { onMount } from 'svelte';
    import { handleFormSubmit, type FieldErrors } from '$lib/formUtils';

    type GlobalTemplateConfig = components['schemas']['GlobalTemplateConfig'];

    let { ...restProps }: ComponentProps<typeof Card.Root> = $props();

    const initialFormData: GlobalTemplateConfig = {
        default_http_port: 80,
        default_https_port: 443,
        is_h1_protocol_enabled: true,
        is_h2_protocol_enabled: true,
        is_h3_protocol_enabled: false,
        timeout: 300000,
        cache_max_entries: 1024
    };

    let formData = $state<GlobalTemplateConfig>({ ...initialFormData });
    let originalData = $state<GlobalTemplateConfig>({ ...initialFormData });

    let isSubmitting = $state(false);
    let isLoading = $state(true);
    let formError = $state('');
    let fieldErrors = $state<FieldErrors>({});

    onMount(async () => {
        await loadGlobalConfig();
    });

    async function loadGlobalConfig() {
        isLoading = true;
        formError = '';

        const result = await handleFormSubmit(() =>
            client.GET(ApiPaths.read_global_config_api_configs_global_get)
        );

        isLoading = false;

        if (result.success && result.data) {
            formData = { ...result.data };
            originalData = { ...result.data };
        } else {
            formError = result.formError ?? 'Failed to load global configuration.';
        }
    }

    const cancel = () => {
        formData = { ...originalData };
        formError = '';
        fieldErrors = {};
    };

    async function handleSubmit(event: Event) {
        event.preventDefault();

        formError = '';
        fieldErrors = {};
        isSubmitting = true;

        const result = await handleFormSubmit(() =>
            client.PATCH(ApiPaths.update_global_config_api_configs_global_patch, {
                body: formData
            })
        );

        isSubmitting = false;

        if (result.success && result.data) {
            toast.success('Global configuration updated successfully!');
            formData = { ...result.data };
            originalData = { ...result.data };
        } else {
            formError = result.formError ?? '';
            fieldErrors = result.fieldErrors ?? {};
        }
    }
</script>

<Card.Root {...restProps}>
    <Card.Header>
        <Card.Title>Global Configuration</Card.Title>
        <Card.Description>
            Configure global settings for the Ferron proxy server including ports, protocols, and
            caching.
        </Card.Description>
    </Card.Header>
    <Card.Content>
        {#if isLoading}
            <div class="flex items-center justify-center py-8">
                <p class="text-muted-foreground">Loading configuration...</p>
            </div>
        {:else}
            {#if formError}
                <div
                    class="mb-4 rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400"
                >
                    {formError}
                </div>
            {/if}

            <form onsubmit={handleSubmit} class="space-y-6">
                <Field.Group>
                    <Field.Field>
                        <Field.Label for="default-http-port">Default HTTP Port</Field.Label>
                        <Input
                            id="default-http-port"
                            type="number"
                            placeholder="80"
                            bind:value={formData.default_http_port}
                            required
                            disabled={isSubmitting}
                            min="1"
                            max="65535"
                        />
                        {#if fieldErrors.default_http_port}
                            <Field.Error>{fieldErrors.default_http_port}</Field.Error>
                        {:else}
                            <Field.Description
                                >The default port for HTTP connections (1-65535).</Field.Description
                            >
                        {/if}
                    </Field.Field>

                    <Field.Field>
                        <Field.Label for="default-https-port">Default HTTPS Port</Field.Label>
                        <Input
                            id="default-https-port"
                            type="number"
                            placeholder="443"
                            bind:value={formData.default_https_port}
                            required
                            disabled={isSubmitting}
                            min="1"
                            max="65535"
                        />
                        {#if fieldErrors.default_https_port}
                            <Field.Error>{fieldErrors.default_https_port}</Field.Error>
                        {:else}
                            <Field.Description
                                >The default port for HTTPS connections (1-65535).</Field.Description
                            >
                        {/if}
                    </Field.Field>

                    <Field.Field orientation="horizontal">
                        <Checkbox
                            id="is-h1-protocol-enabled"
                            bind:checked={formData.is_h1_protocol_enabled}
                            disabled={isSubmitting}
                        />
                        <Field.Content>
                            <Label for="is-h1-protocol-enabled" class="font-normal"
                                >Enable HTTP/1.1 Protocol</Label
                            >
                            <Field.Description
                                >Allow HTTP/1.1 connections to the proxy server.</Field.Description
                            >
                        </Field.Content>
                    </Field.Field>

                    <Field.Field orientation="horizontal">
                        <Checkbox
                            id="is-h2-protocol-enabled"
                            bind:checked={formData.is_h2_protocol_enabled}
                            disabled={isSubmitting}
                        />
                        <Field.Content>
                            <Label for="is-h2-protocol-enabled" class="font-normal"
                                >Enable HTTP/2 Protocol</Label
                            >
                            <Field.Description
                                >Allow HTTP/2 connections to the proxy server.</Field.Description
                            >
                        </Field.Content>
                    </Field.Field>

                    <Field.Field orientation="horizontal">
                        <Checkbox
                            id="is-h3-protocol-enabled"
                            bind:checked={formData.is_h3_protocol_enabled}
                            disabled={isSubmitting}
                        />
                        <Field.Content>
                            <Label for="is-h3-protocol-enabled" class="font-normal"
                                >Enable HTTP/3 Protocol</Label
                            >
                            <Field.Description>
                                Allow HTTP/3 (QUIC) connections to the proxy server.
                            </Field.Description>
                        </Field.Content>
                    </Field.Field>

                    <Field.Field>
                        <Field.Label for="timeout">Timeout (milliseconds)</Field.Label>
                        <Input
                            id="timeout"
                            type="number"
                            placeholder="300000"
                            bind:value={formData.timeout}
                            required
                            disabled={isSubmitting}
                            min="0"
                        />
                        {#if fieldErrors.timeout}
                            <Field.Error>{fieldErrors.timeout}</Field.Error>
                        {:else}
                            <Field.Description>
                                Request timeout in milliseconds (default: 300000 = 5 minutes).
                            </Field.Description>
                        {/if}
                    </Field.Field>

                    <Field.Field>
                        <Field.Label for="cache-max-entries">Cache Max Entries</Field.Label>
                        <Input
                            id="cache-max-entries"
                            type="number"
                            placeholder="1024"
                            bind:value={formData.cache_max_entries}
                            required
                            disabled={isSubmitting}
                            min="0"
                        />
                        {#if fieldErrors.cache_max_entries}
                            <Field.Error>{fieldErrors.cache_max_entries}</Field.Error>
                        {:else}
                            <Field.Description
                                >Maximum number of entries allowed in the cache.</Field.Description
                            >
                        {/if}
                    </Field.Field>
                </Field.Group>

                <Field.Group>
                    <Field.Field>
                        <div class="flex gap-4">
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? 'Saving...' : 'Save Changes'}
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                onclick={cancel}
                                disabled={isSubmitting}
                            >
                                Cancel
                            </Button>
                        </div>
                    </Field.Field>
                </Field.Group>
            </form>
        {/if}
    </Card.Content>
</Card.Root>
