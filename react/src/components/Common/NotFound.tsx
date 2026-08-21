import { Button } from "@/components/ui/button"
import { Link } from "@tanstack/react-router"

const NotFound = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center">
      <p className="font-display text-8xl font-medium leading-none text-primary/80">
        404
      </p>
      <h1 className="mt-6 font-display text-xl font-medium text-foreground">
        This page seems to be missing
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        The letter you're looking for may have been moved or never sent.
      </p>
      <Button variant="outline" asChild className="mt-6">
        <Link to="/">Back home</Link>
      </Button>
    </div>
  )
}

export default NotFound
