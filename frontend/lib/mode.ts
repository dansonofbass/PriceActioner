// Default is independent market viewing, even if an old BACKEND_URL remains set.
export const standalone = process.env.NEXT_PUBLIC_APP_MODE !== 'full';
