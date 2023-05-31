import asyncio
import aiohttp
import aiosmtplib

# ... other imports remain the same

# Async fetch function using aiohttp
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

# Modify api_and_email_task to be an async function
async def api_and_email_task(sem, cityID, city_name, dateFact, tomorrow, recipients, local_tz, utc_offset_seconds):
    async with sem:
        # ... rest of the function remains the same, except for the following changes

        # Replace time.sleep with asyncio.sleep
        await asyncio.sleep(30)

        # Replace requests.get with the fetch function
        async with aiohttp.ClientSession() as session:
            curr_r = await fetch(session, url)
            # ... and similarly for other fetch calls

        # Replace smtplib.SMTP with aiosmtplib.SMTP
        async with aiosmtplib.SMTP(GMAIL_AUTH["mail_server"], 587) as server:
            await server.starttls()
            await server.login(GMAIL_AUTH["mail_username"], GMAIL_AUTH["mail_password"])
            await server.send_message(message)
            logging.info(f"Sent email to {recipient}")

        # ...

# Modify main to create and use an asyncio event loop
def main():
    # ... rest of the function remains the same, until this point

    sem = asyncio.Semaphore(5)

    tasks = []
    for row in tblDimEmailCity_sorted.itertuples(index=True, name="Pandas"):
        recipients = str(getattr(row, "email_set")).split(",")
        cityID = getattr(row, "city_id")
        local_tz = getattr(row, "tz")
        utc_offset_seconds = getattr(row, "utc_offset_seconds")
        city_name = city_dict[str(cityID)]
        logging.info(
            f"cityID={str(cityID)}, city_name={city_name}, local_tz={local_tz}, utc_offset_seconds={utc_offset_seconds}"
        )

        task = api_and_email_task(
            sem,
            cityID,
            city_name,
            dateFact,
            tomorrow,
            recipients,
            local_tz,
            utc_offset_seconds,
        )
        tasks.append(task)

    # Run the tasks concurrently
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))

    # ...

if __name__ == "__main__":
    main()
