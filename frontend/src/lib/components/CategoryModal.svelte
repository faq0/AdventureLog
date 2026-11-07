<script lang="ts">
	import type { Category } from '#lib/types.js';
	import { createEventDispatcher, onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import Close from '~icons/mdi/close';
	let { categories = $bindable([]) }: { categories?: Category[] } = $props();
	const dispatch = createEventDispatcher();
	let dialog: HTMLDialogElement | undefined = $state();
	let query = $state('');
	let newName = $state('');
	let editing: Category | null = $state(null);
	let removing: Category | null = $state(null);
	let busy = $state(false);
	let loading = $state(true);
	let error = $state('');
	let filtered = $derived(
		[...categories]
			.filter((c) => c.display_name.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
			.sort((a, b) => a.display_name.localeCompare(b.display_name))
	);
	function close() {
		dialog?.close();
		dispatch('close');
	}
	onMount(async () => {
		dialog?.showModal();
		try {
			const response = await fetch('/api/categories/');
			if (!response.ok) throw new Error('load');
			categories = await response.json();
		} catch {
			error = $t('adventures.error_occurred');
		} finally {
			loading = false;
		}
	});
	async function save(event: SubmitEvent) {
		event.preventDefault();
		const name = (editing?.display_name || newName).trim();
		if (!name || busy) return;
		busy = true;
		error = '';
		try {
			const response = await fetch(
				editing ? `/api/categories/${editing.id}/` : '/api/categories/',
				{
					method: editing ? 'PATCH' : 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(
						editing
							? { display_name: name }
							: {
									display_name: name,
									name:
										name
											.toLowerCase()
											.replace(/\s+/g, '_')
											.replace(/[^a-z0-9_]/g, '') || name.toLowerCase()
								}
					)
				}
			);
			if (!response.ok) throw new Error('save');
			const result = await response.json();
			categories = editing
				? categories.map((c) => (c.id === result.id ? result : c))
				: [...categories, result];
			editing = null;
			newName = '';
		} catch {
			error = $t('adventures.error_occurred');
		} finally {
			busy = false;
		}
	}
	async function remove() {
		if (!removing || removing.name === 'general' || busy) return;
		busy = true;
		error = '';
		try {
			const response = await fetch(`/api/categories/${removing.id}/`, { method: 'DELETE' });
			if (!response.ok) throw new Error('delete');
			categories = categories.filter((c) => c.id !== removing?.id);
			removing = null;
		} catch {
			error = $t('adventures.error_occurred');
		} finally {
			busy = false;
		}
	}
</script>

<dialog
	class="modal"
	id="category-modal"
	bind:this={dialog}
	oncancel={(event) => {
		event.preventDefault();
		close();
	}}
>
	<div class="modal-box max-w-2xl p-0" aria-labelledby="category-modal-title">
		<header class="flex items-center justify-between gap-4 px-6 py-5 border-b border-base-300">
			<div>
				<h2 id="category-modal-title" class="text-xl font-semibold">
					{$t('categories.manage_categories')}
				</h2>
				<p class="text-sm text-base-content/60 mt-1">
					{$t('adventures.categories')} · {categories.length}
				</p>
			</div>
			<button
				class="btn btn-ghost btn-sm btn-square"
				type="button"
				onclick={close}
				aria-label={$t('about.close')}><Close class="w-5 h-5" /></button
			>
		</header>
		<div class="p-6 space-y-5">
			{#if error}<p class="alert alert-error text-sm" role="alert">{error}</p>{/if}
			<input
				class="input w-full"
				type="search"
				bind:value={query}
				placeholder={$t('navbar.search')}
				aria-label={$t('navbar.search')}
			/>
			<div class="max-h-[45dvh] overflow-y-auto">
				{#if loading}<div class="py-8 text-center">
						<span class="loading loading-spinner loading-sm"></span>
					</div>
				{:else if filtered.length === 0}<p class="py-6 text-sm text-base-content/60">
						{$t('categories.no_categories_found')}
					</p>
				{:else}<ul class="divide-y divide-base-300">
						{#each filtered as category (category.id)}<li class="py-3">
								{#if editing?.id === category.id}
									<form onsubmit={save} class="flex flex-wrap gap-2">
										<input
											class="input input-sm grow"
											aria-label={$t('categories.category_name')}
											bind:value={editing.display_name}
											required
										/><button class="btn btn-primary btn-sm" disabled={busy}
											>{$t('notes.save')}</button
										><button
											type="button"
											class="btn btn-ghost btn-sm"
											onclick={() => (editing = null)}>{$t('adventures.cancel')}</button
										>
									</form>
								{:else if removing?.id === category.id}
									<div class="surface p-4">
										<p class="font-medium">{$t('adventures.remove')} {category.display_name}?</p>
										<p class="text-sm text-base-content/65 mt-1">
											Locations in this category will be moved to General.
										</p>
										<div class="flex justify-end gap-2 mt-3">
											<button
												type="button"
												class="btn btn-ghost btn-sm"
												onclick={() => (removing = null)}>{$t('adventures.cancel')}</button
											><button
												type="button"
												class="btn btn-error btn-sm"
												disabled={busy}
												onclick={remove}>{$t('adventures.remove')}</button
											>
										</div>
									</div>
								{:else}<div class="flex items-center gap-4">
										<div class="min-w-0 flex-1">
											<div class="font-medium truncate">{category.display_name}</div>
											<div class="text-xs text-base-content/55 mt-1">
												{category.num_locations || 0}
												{$t('locations.locations').toLowerCase()}
											</div>
										</div>
										<button
											type="button"
											class="btn btn-ghost btn-sm"
											onclick={() => {
												editing = { ...category };
												removing = null;
											}}>{$t('lodging.edit')}</button
										>{#if category.name !== 'general'}<button
												type="button"
												class="btn btn-ghost btn-sm text-error"
												onclick={() => {
													removing = category;
													editing = null;
												}}>{$t('adventures.remove')}</button
											>{/if}
									</div>{/if}
							</li>{/each}
					</ul>{/if}
			</div>
			<form class="border-t border-base-300 pt-5" onsubmit={save}>
				<label class="field-label" for="new-category-name"
					>{$t('categories.add_new_category')}</label
				>
				<div class="flex gap-2">
					<input
						id="new-category-name"
						class="input min-w-0 grow"
						bind:value={newName}
						placeholder={$t('categories.category_name')}
						disabled={editing !== null}
						required
					/><button class="btn btn-primary" disabled={busy || editing !== null || !newName.trim()}
						>{$t('adventures.add')}</button
					>
				</div>
			</form>
		</div>
	</div>
	<form method="dialog" class="modal-backdrop">
		<button onclick={close}>{$t('about.close')}</button>
	</form>
</dialog>
