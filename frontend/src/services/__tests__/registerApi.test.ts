import { afterEach, expect, it, vi } from 'vitest'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.resetModules()
})

it('uses the authenticated same-origin proxy despite the legacy public API setting', async () => {
  vi.stubEnv('VITE_API_URL', 'https://legacy-public-api.example.com')
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] })
  vi.stubGlobal('fetch', fetchMock)
  const { registerRequest } = await import('../registerApi')

  await registerRequest('test-access-token', '/deals')

  expect(fetchMock).toHaveBeenCalledWith('/api/v1/register/deals', expect.objectContaining({
    cache: 'no-store',
    headers: expect.objectContaining({ Authorization: 'Bearer test-access-token' }),
  }))
})
