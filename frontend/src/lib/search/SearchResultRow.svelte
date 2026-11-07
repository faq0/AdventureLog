<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';
	import { getSearchTypeIcon } from '#lib/search/icons.js';
	import type { SearchEntityType, SearchHit } from '#lib/search/types.js';

	interface Props {
		hit: SearchHit;
		selected?: boolean;
		compact?: boolean;
		spotlight?: boolean;
	}

	let { hit, selected = false, compact = false, spotlight = false }: Props = $props();

	const dispatch = createEventDispatcher<{ select: SearchHit }>();
	let ResultIcon = $derived(getSearchTypeIcon(hit.type));

	function typeLabel(type: SearchEntityType): string {
		const key = `search.types.${type}`;
		const translated = $t(key);
		return translated === key ? type : translated;
	}

	let rowClass = $derived(
		[
			'w-full text-left flex items-center gap-3 transition-colors',
			spotlight
				? 'mx-2 px-3 py-2.5 rounded-xl'
				: compact
					? 'px-4 py-2 rounded-lg'
					: 'px-4 py-3 rounded-lg',
			selected
				? 'bg-primary text-primary-content'
				: spotlight
					? 'bg-base-200/25 hover:bg-base-200/45'
					: 'hover:bg-base-200'
		].join(' ')
	);
</script>

<button type="button" class={rowClass} onclick={() => dispatch('select', hit)}>
	<div
		class="flex shrink-0 items-center justify-center w-8 h-8"
		class:text-primary-content={selected}
		class:text-base-content={!selected}
	>
		<ResultIcon class="w-4 h-4 opacity-60" />
	</div>

	<div class="min-w-0 flex-1">
		<div class="flex items-start justify-between gap-3 min-w-0">
			<div class="min-w-0 flex-1">
				<p class="font-medium truncate leading-snug">{hit.title}</p>
				{#if hit.subtitle}
					<p
						class="truncate leading-snug mt-0.5"
						class:text-sm={spotlight}
						class:opacity-70={selected}
						class:text-base-content={!selected}
						class:opacity-60={!selected}
					>
						{hit.subtitle}
					</p>
				{/if}
			</div>
			<div class="flex flex-wrap items-center justify-end gap-1 shrink-0 max-w-[45%]">
				<span
					class="badge badge-xs whitespace-nowrap"
					class:badge-primary={selected}
					class:badge-ghost={!selected}
				>
					{typeLabel(hit.type)}
				</span>
				{#if hit.meta?.is_visited}
					<span class="badge badge-xs badge-success whitespace-nowrap">{$t('search.visited')}</span>
				{/if}
				{#if hit.meta?.is_shared}
					<span class="badge badge-xs badge-info whitespace-nowrap"
						>{$t('navbar.shared_with_me')}</span
					>
				{/if}
			</div>
		</div>
	</div>
</button>
