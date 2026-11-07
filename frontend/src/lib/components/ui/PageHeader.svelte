<script lang="ts">
	import type { Snippet } from 'svelte';
	let {
		title,
		description = '',
		eyebrow = '',
		children
	}: { title: string; description?: string; eyebrow?: string; children?: Snippet } = $props();
</script>

<header class="page-header">
	<div class="min-w-0">
		{#if eyebrow}<span class="page-eyebrow">{eyebrow}</span>{/if}
		<h1>{title}</h1>
		{#if description}<p>{description}</p>{/if}
	</div>
	{#if children}<div class="page-actions">{@render children()}</div>{/if}
</header>
