package main

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	"github.com/zmb3/spotify/v2"
	spotifyauth "github.com/zmb3/spotify/v2/auth"
)

var ctx = context.Background()

const (
	redirectURI = "http://localhost:8005/callback"
	state = "state"
)

 var (
	auth = spotifyauth.New(spotifyauth.WithClientID(os.Getenv("SPOTIFY_CLIENT_ID")), spotifyauth.WithClientSecret(os.Getenv("SPOTIFY_CLIENT_SECRET")), spotifyauth.WithRedirectURL(redirectURI))
	ch = make(chan *spotify.Client)
)

func main() {
	router := gin.Default()
	// router.SetTrustedProxies([]string{""})

	router.GET("/", healthz)
	router.GET("/healthz", healthz)

	router.GET("/redis", getRedis)

	router.GET("/login", beginAuth)
	router.GET("/callback", completeAuth)
	router.GET("/user", getUser)
	

	router.Run(":8080")
}

func getUser(c *gin.Context) {
	client := <-ch

	user, err := client.CurrentUser(ctx)
	if err != nil {
		fmt.Println("ERROR", err)
	}

	c.JSON(http.StatusOK, gin.H{
		"user": user,
	})
}

func beginAuth(c *gin.Context) {
	url := auth.AuthURL(state)
	fmt.Println("URL", url)
	c.JSON(http.StatusOK, gin.H{
		"url": url,})

	// client := <-ch

	// user, err := client.CurrentUser(ctx)
	// if err != nil {
	// 	log.Fatal(err)
	// }

	// fmt.Println("You are logged in as:", user.ID)
}

func completeAuth(c *gin.Context) {
	// Use the authorization code to get a token
	tok, err := auth.Token(ctx, state, c.Request)
	if err != nil {
		http.Error(c.Writer, "Couldn't get token", http.StatusForbidden)
		return
	}

	client := spotify.New(auth.Client(c, tok))
	go func() {
	ch <- client

	}()
	fmt.Println("CLIENT", client)
	// fmt.Fprintf(c.Writer, "Login Completed!")
	c.JSON(http.StatusOK, gin.H{
		"message": "Login Completed!",})
}

func healthz(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Hello, World!",
	})
}

func connectToRedis() *redis.Client {
	return redis.NewClient(&redis.Options{
		Addr:     "redis:6379",
		Password: "",
		DB:       0,
	})
}

func getKeysFromRedis(client *redis.Client) []string {
	keys := client.Keys(ctx, "*").Val()
	return keys
}

func getRedis(c *gin.Context) {
	client := connectToRedis()
	pong, err := client.Ping(ctx).Result()
	fmt.Println("PONG ERR LINE", pong, err)
	client.Set(ctx, "key", "value", 0)
	val, err := client.Get(ctx, "key").Result()
	if err != nil {
		panic(err)
	}
	fmt.Println("key", val)
	keys := getKeysFromRedis(client)

	c.JSON(http.StatusOK, gin.H{
		"keys": keys,
	})
}