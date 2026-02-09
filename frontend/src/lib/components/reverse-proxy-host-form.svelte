<script lang="ts">
    import { Button } from '$lib/components/ui/button/index.js';
    import * as Card from '$lib/components/ui/card/index.js';
    import { Checkbox } from '$lib/components/ui/checkbox/index.js';
    import * as Field from '$lib/components/ui/field/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Label } from '$lib/components/ui/label/index.js';
    import type { components } from '$lib/api/types';
    import { ApiPaths } from '$lib/api/types';
    import { type ComponentProps, untrack } from 'svelte';
    import client from '$lib/apiClient';
    import { toast } from 'svelte-sonner';
    import { handleFormSubmit, type FieldErrors } from '$lib/formUtils';

    type CreateReverseProxyConfig = components['schemas']['CreateReverseProxyConfig'];
    type UpdateReverseProxyConfig = components['schemas']['UpdateReverseProxyConfig'];

    let {
        initialData,
        onSubmit,
        onCancel,
        ...restProps
    }: ComponentProps<typeof Card.Root> & {
        initialData?: Partial<CreateReverseProxyConfig | UpdateReverseProxyConfig>;
        onSubmit?: (data: CreateReverseProxyConfig | UpdateReverseProxyConfig) => void;
        onCancel?: () => void;
    } = $props();

    const initialFormData: CreateReverseProxyConfig = {
        virtual_host_name: '',
        backend_url: '',
        cache: false,
        cache_max_age: 3600,
        preserve_host_header: false,
        use_unix_socket: false,
        unix_socket_path: ''
    };

    let formData = $state<CreateReverseProxyConfig | UpdateReverseProxyConfig>(
        untrack(() => ({ ...initialFormData, ...initialData }))
    );

    let isSubmitting = $state(false);
    let formError = $state('');
    let fieldErrors = $state<FieldErrors>({});

    const isEditMode = $derived('id' in formData && typeof formData.id === 'number');

    const cancel = () => {
        if (onCancel) {
            onCancel();
            return;
        }

        if (!initialData) {
            formData = { ...initialFormData };
        } else {
            formData = { ...initialFormData, ...initialData };
        }
        formError = '';
        fieldErrors = {};
    };

    async function handleSubmit(event: Event) {
        event.preventDefault();

        formError = '';
        fieldErrors = {};

        if (onSubmit) {
            onSubmit($state.snapshot(formData));
            return;
        }

        isSubmitting = true;

        const result = await handleFormSubmit(() =>
            client.POST(ApiPaths.create_reverse_proxy_config_api_configs_reverse_proxy_post, {
                body: formData as CreateReverseProxyConfig
            })
        );

        isSubmitting = false;

        if (result.success) {
            toast.success('Reverse proxy configuration created successfully!');
            formData = { ...initialFormData };
        } else {
            formError = result.formError ?? '';
            fieldErrors = result.fieldErrors ?? {};
        }
    }
</script>

<Card.Root {...restProps}>
    <Card.Header>
        <Card.Title>Reverse Proxy Configuration</Card.Title>
        <Card.Description
            >Configure a reverse proxy host to route requests to a backend server.</Card.Description
        >
    </Card.Header>
    <Card.Content>
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
                    <Field.Label for="virtual-host-name">Virtual Host Name</Field.Label>
                    <Input
                        id="virtual-host-name"
                        type="text"
                        placeholder="example.com"
                        bind:value={formData.virtual_host_name}
                        required
                        disabled={isSubmitting}
                    />
                    {#if fieldErrors.virtual_host_name}
                        <Field.Error>{fieldErrors.virtual_host_name}</Field.Error>
                    {:else}
                        <Field.Description
                            >The hostname for this reverse proxy configuration.</Field.Description
                        >
                    {/if}
                </Field.Field>

                <Field.Field>
                    <Field.Label for="backend-url">Backend URL</Field.Label>
                    <Input
                        id="backend-url"
                        type="text"
                        placeholder="http://localhost:8000"
                        bind:value={formData.backend_url}
                        required
                        disabled={isSubmitting}
                    />
                    {#if fieldErrors.backend_url}
                        <Field.Error>{fieldErrors.backend_url}</Field.Error>
                    {:else}
                        <Field.Description
                            >The backend server URL to proxy requests to.</Field.Description
                        >
                    {/if}
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox id="cache" bind:checked={formData.cache} disabled={isSubmitting} />
                    <Field.Content>
                        <Label for="cache" class="font-normal">Enable Caching</Label>
                        <Field.Description>
                            Cache responses from the backend server to improve performance.
                        </Field.Description>
                    </Field.Content>
                </Field.Field>

                <Field.Field>
                    <Field.Label for="cache-max-age">Cache Max Age (seconds)</Field.Label>
                    <Input
                        id="cache-max-age"
                        type="number"
                        placeholder="3600"
                        bind:value={formData.cache_max_age}
                        disabled={!formData.cache || isSubmitting}
                        min="0"
                    />
                    {#if fieldErrors.cache_max_age}
                        <Field.Error>{fieldErrors.cache_max_age}</Field.Error>
                    {:else}
                        <Field.Description>
                            How long cached responses should be stored (in seconds).
                        </Field.Description>
                    {/if}
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="preserve-host-header"
                        bind:checked={formData.preserve_host_header}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="preserve-host-header" class="font-normal"
                            >Preserve Host Header</Label
                        >
                        <Field.Description>
                            Forward the original Host header to the backend server.
                        </Field.Description>
                    </Field.Content>
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="use-unix-socket"
                        bind:checked={formData.use_unix_socket}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="use-unix-socket" class="font-normal">Use Unix Socket</Label>
                        <Field.Description>
                            Connect to the backend via a Unix socket instead of HTTP.
                        </Field.Description>
                    </Field.Content>
                </Field.Field>

                <Field.Field>
                    <Field.Label for="unix-socket-path">Unix Socket Path</Field.Label>
                    <Input
                        id="unix-socket-path"
                        type="text"
                        placeholder="/tmp/backend.sock"
                        bind:value={formData.unix_socket_path}
                        disabled={!formData.use_unix_socket || isSubmitting}
                    />
                    {#if fieldErrors.unix_socket_path}
                        <Field.Error>{fieldErrors.unix_socket_path}</Field.Error>
                    {:else}
                        <Field.Description>
                            Path to the Unix socket for backend connection (when using Unix socket).
                        </Field.Description>
                    {/if}
                </Field.Field>
            </Field.Group>

            {#if formError}
                <div
                    class="rounded-lg border border-red-500 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/20 dark:text-red-400"
                >
                    {formError}
                </div>
            {/if}

            <Field.Group>
                <Field.Field>
                    <div class="flex justify-end gap-4">
                        <Button
                            type="button"
                            variant="outline"
                            onclick={cancel}
                            disabled={isSubmitting}
                        >
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting
                                ? isEditMode
                                    ? 'Saving...'
                                    : 'Creating...'
                                : isEditMode
                                  ? 'Save Changes'
                                  : 'Create Reverse Proxy'}
                        </Button>
                    </div>
                </Field.Field>
            </Field.Group>
        </form>
    </Card.Content>
</Card.Root>
