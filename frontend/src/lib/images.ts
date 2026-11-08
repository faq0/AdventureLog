import type { ContentImage, ImageSource } from '#lib/types.js';

export function normalizeContentImage(
	partial: Partial<ContentImage> & Pick<ContentImage, 'id' | 'image'>
): ContentImage {
	return {
		id: partial.id,
		captured_at: partial.captured_at ?? null,
		captured_local: partial.captured_local ?? null,
		captured_timezone: partial.captured_timezone ?? null,
		capture_time_status: partial.capture_time_status ?? 'missing',
		image: partial.image,
		is_primary: partial.is_primary ?? false,
		immich_id: partial.immich_id ?? null,
		source: partial.source ?? 'upload',
		source_url: partial.source_url ?? null,
		latitude: partial.latitude ?? null,
		longitude: partial.longitude ?? null
	};
}

export function googleContentImage(id: string, image: string, isPrimary = false): ContentImage {
	return normalizeContentImage({ id, image, is_primary: isPrimary, source: 'google' });
}

export function defaultImageSource(source?: ImageSource | null): ImageSource {
	return source ?? 'upload';
}
