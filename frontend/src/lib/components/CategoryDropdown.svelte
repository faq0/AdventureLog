<script lang="ts">
	import { onMount, tick } from 'svelte';
	import type { Category } from '#lib/types.js';
	import { t } from 'svelte-i18n';
	import ChevronDown from '~icons/mdi/chevron-down';
	import { shouldFlipDropdownUp } from '#lib/utils/flipDropdown.js';

	let {
		selected_category = $bindable(null),
		searchTerm = $bindable(''),
		id = undefined
	}: { selected_category?: Category | null; searchTerm?: string; id?: string } = $props();
	let categories: Category[] = $state([]);
	let isOpen = $state(false);
	let openUpward = $state(false);
	let dropdownRef: HTMLDivElement | undefined = $state();
	let searchInput: HTMLInputElement | undefined = $state();
	let newName = $state('');
	let busy = $state(false);
	let error = $state('');
	let filtered = $derived(
		[...categories]
			.filter((c) => c.display_name.toLocaleLowerCase().includes(searchTerm.toLocaleLowerCase()))
			.sort(
				(a, b) =>
					(b.num_locations || 0) - (a.num_locations || 0) ||
					a.display_name.localeCompare(b.display_name)
			)
	);

	async function toggle() {
		isOpen = !isOpen;
		if (isOpen) {
			openUpward = shouldFlipDropdownUp(dropdownRef);
			await tick();
			searchInput?.focus();
		}
	}
	function select(category: Category) {
		selected_category = category;
		isOpen = false;
		searchTerm = '';
	}
	async function create() {
		const name = newName.trim();
		if (!name || busy) return;
		const existing = categories.find(
			(c) => c.display_name.toLocaleLowerCase() === name.toLocaleLowerCase()
		);
		if (existing) {
			select(existing);
			newName = '';
			return;
		}
		busy = true;
		error = '';
		try {
			const response = await fetch('/api/categories/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					display_name: name,
					name:
						name
							.toLowerCase()
							.replace(/\s+/g, '_')
							.replace(/[^a-z0-9_]/g, '') || name.toLowerCase()
				})
			});
			if (!response.ok) throw new Error('create');
			const category = await response.json();
			categories = [...categories, category];
			select(category);
			newName = '';
		} catch {
			error = $t('adventures.error_occurred');
		} finally {
			busy = false;
		}
	}
	onMount(() => {
		fetch('/api/categories/')
			.then((response) => {
				if (!response.ok) throw new Error('load');
				return response.json();
			})
			.then((value) => {
				categories = Array.isArray(value) ? value : [];
			})
			.catch(() => {
				error = $t('adventures.error_occurred');
			});
		const outside = (event: PointerEvent) => {
			if (!dropdownRef?.contains(event.target as Node)) isOpen = false;
		};
		document.addEventListener('pointerdown', outside);
		return () => document.removeEventListener('pointerdown', outside);
	});
</script>

<svelte:window
	onkeydown={(event) => {
		if (event.key === 'Escape') isOpen = false;
	}}
/>
<div
	class="dropdown w-full"
	class:dropdown-open={isOpen}
	class:dropdown-top={openUpward}
	bind:this={dropdownRef}
>
	<button
		{id}
		type="button"
		class="input w-full flex items-center justify-between cursor-pointer text-left"
		aria-expanded={isOpen}
		aria-haspopup="listbox"
		onclick={toggle}
		><span class="truncate"
			>{selected_category?.display_name || $t('categories.select_category')}</span
		><ChevronDown class="h-4 w-4 shrink-0 text-base-content/50" /></button
	>
	{#if isOpen}
		<div class="dropdown-content category-menu surface p-3 z-50">
			<input
				aria-label={$t('navbar.search')}
				type="search"
				class="input input-sm w-full mb-2"
				placeholder={$t('navbar.search')}
				bind:value={searchTerm}
				bind:this={searchInput}
			/>
			<div role="listbox" aria-label={$t('categories.select_category')} class="category-list">
				{#each filtered as category (category.id)}<button
						type="button"
						role="option"
						aria-selected={selected_category?.id === category.id}
						class="category-option"
						class:category-selected={selected_category?.id === category.id}
						onclick={() => select(category)}
						><span class="truncate">{category.display_name}</span><span
							class="text-xs text-base-content/45 tabular-nums">{category.num_locations || 0}</span
						></button
					>{/each}
				{#if filtered.length === 0}<p class="text-sm text-base-content/55 p-2">
						{$t('categories.no_categories_found')}
					</p>{/if}
			</div>
			<div class="border-t border-base-300 pt-3 mt-2">
				<label class="field-label" for={`${id || 'category'}-new`}
					>{$t('categories.add_new_category')}</label
				>
				<div class="flex gap-2">
					<input
						id={`${id || 'category'}-new`}
						class="input input-sm min-w-0 flex-1"
						bind:value={newName}
						placeholder={$t('categories.category_name')}
						onkeydown={(event) => {
							if (event.key === 'Enter') {
								event.preventDefault();
								void create();
							}
						}}
					/><button
						type="button"
						class="btn btn-primary btn-sm"
						disabled={busy || !newName.trim()}
						onclick={create}>{busy ? '…' : $t('adventures.add')}</button
					>
				</div>
				{#if error}<p class="text-error text-sm mt-2" role="alert">{error}</p>{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.category-menu {
		width: 100%;
		min-width: 240px;
		margin-top: 0.35rem;
	}
	.category-list {
		max-height: 15rem;
		overflow-y: auto;
	}
	.category-option {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		text-align: left;
		padding: 0.6rem 0.5rem;
		border-radius: 0.35rem;
		font-size: 0.875rem;
		cursor: pointer;
	}
	.category-option:hover,
	.category-selected {
		background: var(--color-base-200);
	}
	@media (max-width: 600px) {
		.category-menu {
			position: fixed;
			inset: auto 1rem 1rem;
			width: auto;
			max-height: 75dvh;
			overflow-y: auto;
			box-shadow: 0 0 0 100vmax #0005;
		}
	}
</style>
