package main

import (
	"context"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

func main() {
	router := gin.Default()
	// router.SetTrustedProxies([]string{""})

	router.GET("/", root)

	router.GET("/redis", getRedis)

	router.Run(":8080")
}

func root(c *gin.Context) {
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