@client.command(aliases=['queue'])
async def list(ctx):
    global video_title
    print(video_title)
    if video_title == "":
        await ctx.send("Nothing is currently in the queue.")
    else:
        await ctx.send("Queue: ")
        embed = discord.Embed(title="Queue:",
                              description=" ",
                              color=0xFF5733)
        if len(queue_of_titles) >= 0:
            i = 0
            for _ in queue_of_titles:
                embed.add_field(name=str(i) + ":",
                                value=queue_of_titles[i])
                i += 1
        else:
            # embed.add_field(name="1: ", value=video_title)
            print("We are in the else statement line:115")
        await ctx.send(embed=embed)

