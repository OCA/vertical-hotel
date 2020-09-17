Module for Complete Hotel management which includes the basic operations at a hotel/apartment.

You can manage:

* Configure Property
* Hotel Configuration
* History of Check In, Check out
* Folio's (i.e. invoicing)
* Payment
* Seasonal room pricing

Seasonal Room Pricing
=====================

To configure seasonal room pricing, in the general settings under 'Sale' check 'Multiple Sales Prices per Product'
(with the default 'Specific price per product' option). This adds pricelists to the room views in the 'Information' tab.

Add a pricelist rule line using the 'Public Pricelist' and configure the time window of the rule.

Now, upon the creation of a folio room line, from a reservation or directly in a folio, the price mentionned in a
pricelist line is used in case the checkin date of the room line falls within the time window of the rule.
