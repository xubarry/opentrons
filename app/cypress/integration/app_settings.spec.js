describe('The Home Page', () => {
  beforeEach(() => {
    cy.visit('/#/menu/app')
    cy.closeAppVersionModal()
  })

  it('shares robot & app analytics', () => {
    cy.get('h3')
      .contains('Privacy Settings')
      .next()
      .within(() => {
        // toggle sharing on
        cy.get('button').click()
        cy.get('[class*="toggled_on"]').should('exist')
        // toggle sharing off
        cy.get('button').click()
        cy.get('[class*="toggled_off"]').should('exist')
      })
  })
})
