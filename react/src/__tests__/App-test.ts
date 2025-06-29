test('loads and displays greeting', async () => {
    // ARRANGE
    render(<Fetch url="/greeting" />)
  
    // ACT
    await userEvent.click(screen.getByText('Load Greeting'))
    await screen.findByRole('heading')
  
    // ASSERT
    expect(screen.getByRole('heading')).toHaveTextContent('hello there')
    expect(screen.getByRole('button')).toBeDisabled()
  })