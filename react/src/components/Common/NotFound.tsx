import { Button } from "@/components/ui/button"
import { Link } from "@tanstack/react-router"

const NotFound = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center text-center">
      <p className="text-8xl font-bold leading-none text-primary mb-4">404</p>
      <p className="text-base text-foreground">Oops!</p>
      <p className="text-base text-muted-foreground">Page not found.</p>
      <Button variant="outline" asChild className="mt-4">
        <Link to="/">Go back</Link>
      </Button>
    </div>
  )
}

export default NotFound
