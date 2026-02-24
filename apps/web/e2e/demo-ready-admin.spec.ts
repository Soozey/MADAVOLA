import { expect, test } from '@playwright/test'

const LOGIN_IDENTIFIER = process.env.PLAYWRIGHT_LOGIN_IDENTIFIER || 'kariboservices@gmail.com'
const LOGIN_PASSWORD = process.env.PLAYWRIGHT_LOGIN_PASSWORD || 'Admin123'

async function loginAndSetupSession(page: any) {
  await page.goto('/login')
  await expect(page.getByTestId('login-form')).toBeVisible()
  await page.getByTestId('login-identifier').fill(LOGIN_IDENTIFIER)
  await page.getByTestId('login-password').fill(LOGIN_PASSWORD)
  await page.getByTestId('login-submit').click()

  await expect(page).toHaveURL(/\/select-role/)
  await expect(page.getByText(/Choisir votre role/i)).toBeVisible()

  await page.getByLabel('Rechercher un role').fill('admin')
  const adminRow = page.locator('[data-testid="role-row-admin"]')
  if (await adminRow.count()) {
    await adminRow.first().click()
  } else {
    await page.locator('[data-testid^="role-row-"]').first().click()
  }
  await page.getByTestId('role-validate').click()

  await expect(page).toHaveURL(/\/select-filiere/)
  await page.getByTestId('filiere-choice-or').click()
  await page.getByTestId('filiere-validate').click()
  await expect(page).toHaveURL(/\/home/)
  await expect(page.getByRole('heading', { name: /Accueil/i })).toBeVisible()
}

test.describe('Demo ready - parcours ecran par ecran (admin)', () => {
  test('Acteurs / Lots / Transactions / Exports / Docs / Carte / Queue Commune', async ({ page }) => {
    await loginAndSetupSession(page)

    const checks: Array<{ path: string; heading: RegExp }> = [
      { path: '/actors', heading: /(Acteurs|Creation ou modification de compte)/i },
      { path: '/lots', heading: /^Lots$/i },
      { path: '/transactions', heading: /^Transactions$/i },
      { path: '/exports', heading: /^Dossiers export$/i },
      { path: '/documents', heading: /^Documents$/i },
      { path: '/ma-carte', heading: /^Ma carte$/i },
      { path: '/or-compliance', heading: /^Demandes de cartes OR$/i },
    ]

    for (const check of checks) {
      await page.goto(check.path)
      await expect(page).toHaveURL(new RegExp(check.path.replace('/', '\\/')))
      await expect(page.getByRole('heading', { level: 1, name: check.heading })).toBeVisible()
      await expect(page.locator('text=Non connecte')).toHaveCount(0)
      await expect(page.locator('text=Erreur reseau')).toHaveCount(0)
      await expect(page.locator('text=token_invalide')).toHaveCount(0)
    }
  })
})
