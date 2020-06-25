describe('The Home Page', () => {
  beforeEach(() => {
    cy.visit('/')
    cy.closeAppVersionModal()
    cy.visit('/#/menu/resources')
  })

  it('links to support articles', () => {
    cy.contains('Support Articles')
    cy.get('[href="https://support.opentrons.com/ot-2"]').should('exist')
  })

  it('links to protocol library', () => {
    cy.contains('Protocol Library')
    cy.get('[href="https://protocols.opentrons.com/"]').should('exist')
  })

  it('links to protocol API documentation', () => {
    cy.contains('Python Protocol API Documentation')
    cy.get('[href="https://docs.opentrons.com/"]').should('exist')
  })
})
