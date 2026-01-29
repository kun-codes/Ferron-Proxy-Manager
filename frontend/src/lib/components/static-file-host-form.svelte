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

    type CreateStaticFileConfig = components['schemas']['CreateStaticFileConfig'];
    type UpdateStaticFileConfig = components['schemas']['UpdateStaticFileConfig'];

    let {
        initialData,
        onSubmit,
        onCancel,
        ...restProps
    }: ComponentProps<typeof Card.Root> & {
        initialData?: Partial<CreateStaticFileConfig | UpdateStaticFileConfig>;
        onSubmit?: (data: CreateStaticFileConfig | UpdateStaticFileConfig) => void;
        onCancel?: () => void;
    } = $props();

    const initialFormData: CreateStaticFileConfig = {
        virtual_host_name: '',
        static_files_dir: '',
        cache: false,
        cache_max_age: 3600,
        use_spa: false,
        compressed: true,
        directory_listing: false,
        precompressed: false
    };

    let formData = $state<CreateStaticFileConfig | UpdateStaticFileConfig>(
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
            client.POST(ApiPaths.create_static_file_config_api_configs_static_file_post, {
                body: formData as CreateStaticFileConfig
            })
        );

        isSubmitting = false;

        if (result.success) {
            toast.success('Static file server configuration created successfully!');
            formData = { ...initialFormData };
        } else {
            formError = result.formError ?? '';
            fieldErrors = result.fieldErrors ?? {};
        }
    }
</script>

<Card.Root {...restProps}>
    <Card.Header>
        <Card.Title>Static File Configuration</Card.Title>
        <Card.Description>
            Configure a static file server to serve files from a directory.
        </Card.Description>
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
                            >The hostname for this static file server.</Field.Description
                        >
                    {/if}
                </Field.Field>

                <Field.Field>
                    <Field.Label for="static-files-dir">Static Files Directory</Field.Label>
                    <Input
                        id="static-files-dir"
                        type="text"
                        placeholder="/var/www/html"
                        bind:value={formData.static_files_dir}
                        required
                        disabled={isSubmitting}
                    />
                    {#if fieldErrors.static_files_dir}
                        <Field.Error>{fieldErrors.static_files_dir}</Field.Error>
                    {:else}
                        <Field.Description>
                            The directory path where static files are located.
                        </Field.Description>
                    {/if}
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox id="cache" bind:checked={formData.cache} disabled={isSubmitting} />
                    <Field.Content>
                        <Label for="cache" class="font-normal">Enable Caching</Label>
                        <Field.Description
                            >Cache static files to improve performance.</Field.Description
                        >
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
                    />
                    {#if fieldErrors.cache_max_age}
                        <Field.Error>{fieldErrors.cache_max_age}</Field.Error>
                    {:else}
                        <Field.Description>
                            How long cached files should be stored (in seconds).
                        </Field.Description>
                    {/if}
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="use-spa"
                        bind:checked={formData.use_spa}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="use-spa" class="font-normal">Single Page Application Mode</Label
                        >
                        <Field.Description>
                            Serve index.html for all routes (useful for SPAs like React, Vue, etc.).
                        </Field.Description>
                    </Field.Content>
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="compressed"
                        bind:checked={formData.compressed}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="compressed" class="font-normal">Enable Compression</Label>
                        <Field.Description
                            >Compress files on-the-fly using gzip or brotli.</Field.Description
                        >
                    </Field.Content>
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="directory-listing"
                        bind:checked={formData.directory_listing}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="directory-listing" class="font-normal">Directory Listing</Label>
                        <Field.Description>
                            Show directory contents when accessing a directory URL.
                        </Field.Description>
                    </Field.Content>
                </Field.Field>

                <Field.Field orientation="horizontal">
                    <Checkbox
                        id="precompressed"
                        bind:checked={formData.precompressed}
                        disabled={isSubmitting}
                    />
                    <Field.Content>
                        <Label for="precompressed" class="font-normal">Precompressed Files</Label>
                        <Field.Description>Serve pre-compressed files.</Field.Description>
                    </Field.Content>
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
                                  : 'Create Static File Server'}
                        </Button>
                    </div>
                </Field.Field>
            </Field.Group>
        </form>
    </Card.Content>
</Card.Root>
