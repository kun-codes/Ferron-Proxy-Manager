<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import ArrowRightLeft from '@lucide/svelte/icons/arrow-right-left';
	import Gauge from '@lucide/svelte/icons/gauge';
	import FileText from '@lucide/svelte/icons/file-text';
	import Code from '@lucide/svelte/icons/code';

	type ConfigType = 'reverse-proxy' | 'load-balancer' | 'static-file';

	interface Props {
		selected: ConfigType;
		onselect: (type: ConfigType) => void;
	}

	let { selected, onselect }: Props = $props();

	const configs = [
		{
			type: 'reverse-proxy' as ConfigType,
			title: 'Reverse Proxy',
			description: 'Proxy requests to backend services with customizable settings',
			icon: ArrowRightLeft,
			complexity: 'Intermediate'
		},
		{
			type: 'load-balancer' as ConfigType,
			title: 'Load Balancer',
			description: 'Balance traffic across multiple backend servers',
			icon: Gauge,
			complexity: 'Advanced'
		},
		{
			type: 'static-file' as ConfigType,
			title: 'Static Site',
			description: 'Optimized configuration for static websites with caching',
			icon: FileText,
			complexity: 'Simple'
		}
	];
</script>

<div class="space-y-4">
	<div>
		<h3 class="flex items-center gap-2 text-sm font-medium">
			<Code class="h-4 w-4" />
			Configuration Content
		</h3>
	</div>

	<div class="space-y-3">
		<p class="text-sm text-muted-foreground">Create Configuration Using Template</p>
		<div class="grid gap-3">
			{#each configs as config}
				<button
					type="button"
					onclick={() => onselect(config.type)}
					class="text-left transition-colors"
				>
					<Card.Root
						class={selected === config.type
							? 'border-primary bg-primary/5'
							: 'hover:border-primary/50'}
					>
						<Card.Header class="p-4">
							<div class="flex items-start justify-between gap-2">
								<div class="flex items-center gap-2">
								<config.icon class="h-4 w-4 text-muted-foreground" />
									<Card.Title class="text-sm font-medium">{config.title}</Card.Title>
								</div>
							</div>
							<Card.Description class="text-xs">{config.description}</Card.Description>
							<div class="pt-1">
								<span class="text-xs text-muted-foreground">{config.complexity}</span>
							</div>
						</Card.Header>
					</Card.Root>
				</button>
			{/each}
		</div>
	</div>
</div>
