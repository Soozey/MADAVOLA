import { expect, test } from '@playwright/test'

const LOGIN_IDENTIFIER = process.env.PLAYWRIGHT_LOGIN_IDENTIFIER || 'admin@madavola.mg'
const LOGIN_PASSWORD = process.env.PLAYWRIGHT_LOGIN_PASSWORD || 'admin123'

test.describe('Flux Auth Mobile - Role -> Filiere', () => {
  test('login -> role Commune -> filiere -> dashboard', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByTestId('login-form')).toBeVisible()
    await page.getByTestId('login-identifier').fill(LOGIN_IDENTIFIER)
    await page.getByTestId('login-password').fill(LOGIN_PASSWORD)
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL(/\/select-role/)
    await expect(page.getByText(/Choisir votre role/i)).toBeVisible()

    const communeRoleButton = page.locator('[data-testid^="role-choose-commune"]').first()
    if (await communeRoleButton.count()) {
      await communeRoleButton.click()
    } else {
      await page.getByLabel('Rechercher un role').fill('commune')
      await page.locator('[data-testid^="role-row-"]').first().click()
    }

    await page.getByTestId('role-validate').click()
    await expect(page).toHaveURL(/\/select-filiere/)

    const filiereChoice = page.getByTestId('filiere-choice-or')
    await filiereChoice.click()
    await page.getByTestId('filiere-validate').click()

    await expect(page).toHaveURL(/\/home/)
    await expect(page.getByText(/Role choisi:/i)).toBeVisible()
    await expect(page.getByText(/Filiere choisie:/i)).toBeVisible()
  })
})

