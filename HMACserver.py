from socket import *
import encryption, hashlib, hmac
import sqlite3


def verify(message, signature):
    secret = b'Macar0n11nAP0t'
    computed_sha = hmac.new(secret, message, digestmod=hashlib.sha3_512).digest()

    if signature != computed_sha:
        return False
    else:
        return True


# create a socket object
s = socket()
try:
    s.setblocking(True)
    s.bind(("localhost", 8888))
    s.listen(5)
    print("HMAC Server Running...")

    while True:
        c, a = s.accept()

        # prints address that connection was received from
        print("Received connection from", a[0])

        message = "Connected to HMAC Server. Hello " + a[0]
        bytesvalue = message.encode('utf-8')
        c.send(bytesvalue)

        # receive bid request
        bid_request = c.recv(2048)

        # decrypt and authenticate bid request
        bidEncrypted = bid_request[:len(bid_request) - 64]
        tag = bid_request[-64:]
        bid = bidEncrypted
        print('Encrypted Bid: ', bidEncrypted)
        try:
            bid = bytes(encryption.cipher.decrypt(bidEncrypted).encode('utf-8'))
            print('Unencrypted Bid: ', bid)
        except:
            print('Bid could not be decrypted.')

        if not verify(bid, tag):
            print('Unauthenticated Bid received! Be on alert! Watch out for bad guys !!!')

        else:
            print('bid authenticated ', bid)

            delim = ','
            bid = bid.decode('utf-8')
            bid = bid.split(delim)
            print(bid)
            bidderId = int(bid[0])
            itemId = int(bid[1])
            bidAmt = int(bid[2])

            user_exists = False
            valid_bid = False
            item_exists = False

            try:
                # open Bidder.db
                con = sqlite3.connect('Bidder.db')

                # create cursor for statement execution
                cur = con.cursor()

                # validate bidderId
                cur.execute('select * from Bidder where BidderId = ?', [bidderId])
                row = cur.fetchone()
                if row is not None:  # bidder exists
                    user_exists = True
                    row = list(row)
                else:
                    print("User does not exist.")

                # validate bid amount is less than PrequalifiedUpperLimit

                if row is not None and bidAmt < int(row[3]):
                    valid_bid = True
                elif row is None:
                    print("Cannot check prequalified upper limit: user does not exist.")
                else:
                    print("Bid Amount higher than the allowed prequalified upper limit.")

                # validate itemId
                cur.execute('select * from AuctionItem where ItemId = ?', [itemId])
                row = cur.fetchone()
                if row is not None:  # item exists
                    row = list(row)
                    item_exists = True
                else:
                    print("Item does not exist.")

                # validate bid amount is greater than the item's LowestBidLimit
                if row is not None and bidAmt > int(row[3]):
                    valid_bid = True
                elif row is None:
                    print("Cannot check lowest bid limit: item does not exist.")
                else:
                    print("Bid Amount is lower than the item's lowest bid limit.")

                # validate bid amount is greater than the item's HighestBidderAmount
                if row is not None and bidAmt > int(row[5]):
                    valid_bid = True
                elif row is None:
                    print("Cannot check highest bidder amount: item does not exist.")
                else:
                    print("Bid Amount is lower than the item's highest bidder amount.")

                if user_exists and item_exists and valid_bid:
                    cur.execute('''UPDATE AuctionItem
                                SET HighestBidderAmount = ?,
                                    HighestBidderId = ?
                                WHERE
                                    ItemId = ? ''', (bidAmt, bidderId, itemId))
                    cur.execute('select * from AuctionItem')
                    con.commit()
                    print("Bid Success!")
                else:
                    print("Bid Failed!")


            except:
                con.rollback()
                print("Error accessing Bidder.db")

            finally:
                con.close()

except error as e:
    print("Error:", e)
    exit(1)
finally:
    s.close()
