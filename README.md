# USCI-Dynamodb_Lambda_SES

Use SES to form a lambda function used as the trigger of Dynamodb.

If "MODIFY" event occured within databse, the function acquires neccessary product information and join it with related users information from Dynamodb stream logs.

After that, form a email using SES and send to target user who subscribed the specific product.
