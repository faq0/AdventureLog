<script lang="ts">
	interface Props {
		padding?: string;
		className?: string;
		id?: string | undefined;
		children?: import('svelte').Snippet;
	}

	let { padding = 'p-6', className = '', id = undefined, children }: Props = $props();
</script>

<div {id} class="surface {padding} {className}">
	{@render children?.()}
</div>
