<script lang="ts">
    import { Button } from '$lib/components/ui/button/index.js';
    import Trash2 from '@lucide/svelte/icons/trash-2';
    import Edit from '@lucide/svelte/icons/edit';
    
    let { host, onEdit, onDelete } = $props();

    let isDeleteConfirm = $state(false);

    function handleDelete() {
        if (isDeleteConfirm) {
            onDelete(host);
            isDeleteConfirm = false;
        } else {
            isDeleteConfirm = true;
            // Auto reset confirmation after 3 seconds
            setTimeout(() => {
                isDeleteConfirm = false;
            }, 3000);
        }
    }
</script>

<div class="flex items-center gap-2">
    <Button variant="outline" size="icon" onclick={() => onEdit(host)}>
        <Edit class="h-4 w-4" />
        <span class="sr-only">Edit</span>
    </Button>
    <Button 
        variant={isDeleteConfirm ? "destructive" : "outline"} 
        size="icon" 
        onclick={handleDelete}
        class={isDeleteConfirm ? "bg-red-600 hover:bg-red-700 text-white" : ""}
    >
        <Trash2 class="h-4 w-4" />
        <span class="sr-only">Delete</span>
    </Button>
</div>
