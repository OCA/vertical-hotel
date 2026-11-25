-- Odoo 19.0 source database for the "Import from Odoo 19" test.
--
-- Made with Odoo 19.0 and the OCA hotel module 19.0.1.0.0 (no demo data):
-- a floor, a room type, an amenity, a service, two rooms, two customers, a
-- folio confirmed and invoiced (posted invoice) and a folio confirmed but
-- not invoiced. Only the tables the import reads are kept, as Odoo 19.0
-- creates them (all their columns), without constraints and indexes, with
-- the rows the import needs; passwords and configuration are cleared.
--


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE TABLE public.account_move (
    id integer NOT NULL,
    sequence_number integer,
    message_main_attachment_id integer,
    journal_id integer NOT NULL,
    company_id integer,
    origin_payment_id integer,
    statement_line_id integer,
    tax_cash_basis_rec_id integer,
    tax_cash_basis_origin_move_id integer,
    auto_post_origin_id integer,
    secure_sequence_number integer,
    invoice_payment_term_id integer,
    partner_id integer,
    commercial_partner_id integer,
    partner_shipping_id integer,
    partner_bank_id integer,
    fiscal_position_id integer,
    preferred_payment_method_line_id integer,
    currency_id integer NOT NULL,
    reversed_entry_id integer,
    invoice_user_id integer,
    invoice_incoterm_id integer,
    invoice_cash_rounding_id integer,
    create_uid integer,
    write_uid integer,
    sequence_prefix character varying,
    access_token character varying,
    name character varying,
    ref character varying,
    state character varying NOT NULL,
    move_type character varying NOT NULL,
    auto_post character varying NOT NULL,
    inalterable_hash character varying,
    payment_reference character varying,
    qr_code_method character varying,
    payment_state character varying,
    invoice_source_email character varying,
    invoice_partner_display_name character varying,
    invoice_origin character varying,
    incoterm_location character varying,
    date date NOT NULL,
    auto_post_until date,
    invoice_date date,
    invoice_date_due date,
    delivery_date date,
    taxable_supply_date date,
    sending_data jsonb,
    narration text,
    invoice_currency_rate numeric,
    amount_untaxed numeric,
    amount_tax numeric,
    amount_total numeric,
    amount_residual numeric,
    amount_untaxed_signed numeric,
    amount_untaxed_in_currency_signed numeric,
    amount_tax_signed numeric,
    amount_total_signed numeric,
    amount_total_in_currency_signed numeric,
    amount_residual_signed numeric,
    quick_edit_total_amount numeric,
    always_tax_exigible boolean,
    checked boolean,
    posted_before boolean,
    made_sequence_gap boolean,
    is_manually_modified boolean,
    is_move_sent boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    campaign_id integer,
    source_id integer,
    medium_id integer,
    team_id integer
);

CREATE SEQUENCE public.account_move_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.account_move_id_seq OWNED BY public.account_move.id;

CREATE TABLE public.account_move_line (
    id integer NOT NULL,
    move_id integer NOT NULL,
    journal_id integer,
    company_id integer,
    company_currency_id integer,
    sequence integer,
    account_id integer,
    currency_id integer NOT NULL,
    partner_id integer,
    reconcile_model_id integer,
    payment_id integer,
    statement_line_id integer,
    statement_id integer,
    group_tax_id integer,
    tax_line_id integer,
    tax_group_id integer,
    tax_repartition_line_id integer,
    full_reconcile_id integer,
    product_id integer,
    product_uom_id integer,
    create_uid integer,
    write_uid integer,
    move_name character varying,
    parent_state character varying,
    ref character varying,
    name character varying,
    matching_number character varying,
    display_type character varying NOT NULL,
    date date,
    invoice_date date,
    date_maturity date,
    discount_date date,
    analytic_distribution jsonb,
    extra_tax_data jsonb,
    debit numeric,
    credit numeric,
    balance numeric,
    amount_currency numeric,
    tax_base_amount numeric,
    amount_residual numeric,
    amount_residual_currency numeric,
    quantity numeric,
    price_unit numeric,
    price_subtotal numeric,
    price_total numeric,
    discount numeric,
    discount_amount_currency numeric,
    discount_balance numeric,
    is_storno boolean,
    is_imported boolean,
    reconciled boolean,
    collapse_composition boolean,
    collapse_prices boolean,
    no_followup boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    deductible_amount double precision,
    cogs_origin_id integer,
    is_downpayment boolean,
    CONSTRAINT account_move_line_check_accountable_required_fields CHECK ((((display_type)::text = ANY (ARRAY[('line_section'::character varying)::text, ('line_subsection'::character varying)::text, ('line_note'::character varying)::text])) OR (account_id IS NOT NULL))),
    CONSTRAINT account_move_line_check_amount_currency_balance_sign CHECK ((((display_type)::text = ANY (ARRAY[('line_section'::character varying)::text, ('line_subsection'::character varying)::text, ('line_note'::character varying)::text])) OR (((balance <= (0)::numeric) AND (amount_currency <= (0)::numeric)) OR ((balance >= (0)::numeric) AND (amount_currency >= (0)::numeric))))),
    CONSTRAINT account_move_line_check_credit_debit CHECK ((((display_type)::text = ANY (ARRAY[('line_section'::character varying)::text, ('line_subsection'::character varying)::text, ('line_note'::character varying)::text])) OR ((credit * debit) = (0)::numeric))),
    CONSTRAINT account_move_line_check_non_accountable_fields_null CHECK ((((display_type)::text <> ALL (ARRAY[('line_section'::character varying)::text, ('line_subsection'::character varying)::text, ('line_note'::character varying)::text])) OR ((amount_currency = (0)::numeric) AND (debit = (0)::numeric) AND (credit = (0)::numeric) AND (account_id IS NULL))))
);

CREATE SEQUENCE public.account_move_line_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.account_move_line_id_seq OWNED BY public.account_move_line.id;

CREATE TABLE public.account_tax (
    id integer NOT NULL,
    company_id integer NOT NULL,
    sequence integer NOT NULL,
    tax_group_id integer NOT NULL,
    cash_basis_transition_account_id integer,
    country_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    type_tax_use character varying NOT NULL,
    tax_scope character varying,
    amount_type character varying NOT NULL,
    price_include_override character varying,
    tax_exigibility character varying,
    name jsonb NOT NULL,
    description jsonb,
    invoice_label jsonb,
    invoice_legal_notes jsonb,
    amount numeric NOT NULL,
    is_domestic boolean,
    active boolean,
    include_base_amount boolean,
    is_base_affected boolean,
    analytic boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    ubl_cii_tax_category_code character varying,
    ubl_cii_tax_exemption_reason_code character varying
);

CREATE SEQUENCE public.account_tax_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.account_tax_id_seq OWNED BY public.account_tax.id;

CREATE TABLE public.account_tax_sale_order_line_rel (
    sale_order_line_id integer NOT NULL,
    account_tax_id integer NOT NULL
);

CREATE TABLE public.folio_room_line (
    id integer NOT NULL,
    room_id integer,
    folio_id integer,
    create_uid integer,
    write_uid integer,
    check_in timestamp without time zone NOT NULL,
    check_out timestamp without time zone NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.folio_room_line_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.folio_room_line_id_seq OWNED BY public.folio_room_line.id;

CREATE TABLE public.hotel_floor (
    id integer NOT NULL,
    sequence integer,
    create_uid integer,
    write_uid integer,
    name character varying NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_floor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_floor_id_seq OWNED BY public.hotel_floor.id;

CREATE TABLE public.hotel_folio (
    id integer NOT NULL,
    order_id integer NOT NULL,
    hotel_invoice_id integer,
    create_uid integer,
    write_uid integer,
    name character varying,
    hotel_policy character varying,
    checkin_date timestamp without time zone NOT NULL,
    checkout_date timestamp without time zone NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    duration double precision,
    duration_dummy double precision
);

CREATE SEQUENCE public.hotel_folio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_folio_id_seq OWNED BY public.hotel_folio.id;

CREATE TABLE public.hotel_folio_line (
    id integer NOT NULL,
    order_line_id integer NOT NULL,
    folio_id integer,
    create_uid integer,
    write_uid integer,
    is_reserved boolean,
    checkin_date timestamp without time zone NOT NULL,
    checkout_date timestamp without time zone NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_folio_line_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_folio_line_id_seq OWNED BY public.hotel_folio_line.id;

CREATE TABLE public.hotel_room (
    id integer NOT NULL,
    product_id integer NOT NULL,
    floor_id integer,
    max_adult integer,
    max_child integer,
    room_categ_id integer NOT NULL,
    capacity integer NOT NULL,
    product_manager integer,
    create_uid integer,
    write_uid integer,
    status character varying,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE TABLE public.hotel_room_amenities (
    id integer NOT NULL,
    product_id integer NOT NULL,
    amenities_categ_id integer NOT NULL,
    product_manager integer,
    create_uid integer,
    write_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_room_amenities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_room_amenities_id_seq OWNED BY public.hotel_room_amenities.id;

CREATE TABLE public.hotel_room_amenities_type (
    id integer NOT NULL,
    amenity_id integer,
    product_categ_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_room_amenities_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_room_amenities_type_id_seq OWNED BY public.hotel_room_amenities_type.id;

CREATE TABLE public.hotel_room_hotel_room_amenities_rel (
    hotel_room_id integer NOT NULL,
    hotel_room_amenities_id integer NOT NULL
);

CREATE SEQUENCE public.hotel_room_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_room_id_seq OWNED BY public.hotel_room.id;

CREATE TABLE public.hotel_room_type (
    id integer NOT NULL,
    categ_id integer,
    product_categ_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_room_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_room_type_id_seq OWNED BY public.hotel_room_type.id;

CREATE TABLE public.hotel_service_line (
    id integer NOT NULL,
    service_line_id integer NOT NULL,
    folio_id integer,
    create_uid integer,
    write_uid integer,
    ser_checkin_date timestamp without time zone,
    ser_checkout_date timestamp without time zone,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_service_line_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_service_line_id_seq OWNED BY public.hotel_service_line.id;

CREATE TABLE public.hotel_service_type (
    id integer NOT NULL,
    service_id integer,
    product_categ_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_service_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_service_type_id_seq OWNED BY public.hotel_service_type.id;

CREATE TABLE public.hotel_services (
    id integer NOT NULL,
    product_id integer NOT NULL,
    service_categ_id integer NOT NULL,
    product_manager integer,
    create_uid integer,
    write_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.hotel_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.hotel_services_id_seq OWNED BY public.hotel_services.id;

CREATE TABLE public.ir_attachment (
    id integer NOT NULL,
    res_id integer,
    company_id integer,
    file_size integer,
    create_uid integer,
    write_uid integer,
    name character varying NOT NULL,
    res_model character varying,
    res_field character varying,
    type character varying NOT NULL,
    url character varying(1024),
    access_token character varying,
    store_fname character varying,
    checksum character varying(40),
    mimetype character varying,
    description text,
    index_content text,
    public boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    db_datas bytea,
    original_id integer
);

CREATE SEQUENCE public.ir_attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.ir_attachment_id_seq OWNED BY public.ir_attachment.id;

CREATE TABLE public.ir_config_parameter (
    id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    key character varying NOT NULL,
    value text NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.ir_config_parameter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.ir_config_parameter_id_seq OWNED BY public.ir_config_parameter.id;

CREATE TABLE public.ir_module_module (
    id integer NOT NULL,
    create_uid integer,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    write_uid integer,
    website character varying,
    summary jsonb,
    name character varying NOT NULL,
    author character varying,
    icon character varying,
    state character varying(16),
    latest_version character varying,
    shortdesc jsonb,
    category_id integer,
    description jsonb,
    application boolean DEFAULT false,
    demo boolean DEFAULT false,
    web boolean DEFAULT false,
    license character varying(32),
    sequence integer DEFAULT 100,
    auto_install boolean DEFAULT false,
    to_buy boolean DEFAULT false,
    maintainer character varying,
    published_version character varying,
    url character varying,
    contributors text,
    menus_by_module text,
    reports_by_module text,
    views_by_module text,
    module_type character varying,
    imported boolean
);

CREATE SEQUENCE public.ir_module_module_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.ir_module_module_id_seq OWNED BY public.ir_module_module.id;

CREATE TABLE public.product_category (
    id integer NOT NULL,
    parent_id integer,
    create_uid integer,
    write_uid integer,
    name character varying NOT NULL,
    complete_name character varying,
    parent_path character varying,
    product_properties_definition jsonb,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    property_account_income_categ_id jsonb,
    property_account_expense_categ_id jsonb,
    removal_strategy_id integer,
    packaging_reserve_method character varying,
    property_valuation jsonb,
    property_cost_method jsonb,
    property_stock_journal jsonb,
    property_stock_valuation_account_id jsonb,
    property_price_difference_account_id jsonb
);

CREATE SEQUENCE public.product_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.product_category_id_seq OWNED BY public.product_category.id;

CREATE TABLE public.product_pricelist (
    id integer NOT NULL,
    sequence integer,
    currency_id integer NOT NULL,
    company_id integer,
    create_uid integer,
    write_uid integer,
    name jsonb NOT NULL,
    active boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.product_pricelist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.product_pricelist_id_seq OWNED BY public.product_pricelist.id;

CREATE TABLE public.product_product (
    id integer NOT NULL,
    product_tmpl_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    default_code character varying,
    barcode character varying,
    combination_indices character varying,
    standard_price jsonb,
    volume numeric,
    weight numeric,
    active boolean,
    can_image_variant_1024_be_zoomed boolean,
    is_favorite boolean,
    is_in_selected_section_of_order boolean,
    write_date timestamp without time zone,
    create_date timestamp without time zone,
    lot_properties_definition jsonb,
    isroom boolean,
    iscategid boolean,
    isservice boolean
);

CREATE SEQUENCE public.product_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.product_product_id_seq OWNED BY public.product_product.id;

CREATE TABLE public.product_supplier_taxes_rel (
    prod_id integer NOT NULL,
    tax_id integer NOT NULL
);

CREATE TABLE public.product_taxes_rel (
    prod_id integer NOT NULL,
    tax_id integer NOT NULL
);

CREATE TABLE public.product_template (
    id integer NOT NULL,
    sequence integer,
    categ_id integer,
    uom_id integer NOT NULL,
    company_id integer,
    color integer,
    create_uid integer,
    write_uid integer,
    type character varying NOT NULL,
    service_tracking character varying NOT NULL,
    default_code character varying,
    name jsonb NOT NULL,
    description jsonb,
    description_purchase jsonb,
    description_sale jsonb,
    product_properties jsonb,
    list_price numeric,
    volume numeric,
    weight numeric,
    sale_ok boolean,
    purchase_ok boolean,
    active boolean,
    can_image_1024_be_zoomed boolean,
    has_configurable_attributes boolean,
    is_favorite boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    property_account_income_id jsonb,
    property_account_expense_id jsonb,
    sale_delay integer,
    lot_sequence_id integer,
    tracking character varying NOT NULL,
    responsible_id jsonb,
    property_stock_production jsonb,
    property_stock_inventory jsonb,
    description_picking jsonb,
    description_pickingout jsonb,
    description_pickingin jsonb,
    is_storable boolean,
    property_price_difference_account_id jsonb,
    lot_valuated boolean,
    service_type character varying,
    expense_policy character varying,
    invoice_policy character varying,
    sale_line_warn_msg text,
    project_id jsonb,
    project_template_id jsonb,
    task_template_id jsonb
);

CREATE SEQUENCE public.product_template_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.product_template_id_seq OWNED BY public.product_template.id;

CREATE TABLE public.res_company (
    id integer NOT NULL,
    name character varying NOT NULL,
    partner_id integer NOT NULL,
    currency_id integer NOT NULL,
    sequence integer,
    create_date timestamp without time zone,
    parent_path character varying,
    parent_id integer,
    paperformat_id integer,
    external_report_layout_id integer,
    create_uid integer,
    write_uid integer,
    email character varying,
    phone character varying,
    font character varying,
    primary_color character varying,
    secondary_color character varying,
    layout_background character varying NOT NULL,
    report_header jsonb,
    report_footer jsonb,
    company_details jsonb,
    active boolean,
    uses_default_logo boolean,
    write_date timestamp without time zone,
    logo_web bytea,
    nomenclature_id integer,
    resource_calendar_id integer,
    alias_domain_id integer,
    email_primary_color character varying,
    email_secondary_color character varying,
    iap_enrich_auto_done boolean,
    snailmail_color boolean,
    snailmail_cover boolean,
    snailmail_duplex boolean,
    fiscalyear_last_day integer NOT NULL,
    transfer_account_id integer,
    default_cash_difference_income_account_id integer,
    default_cash_difference_expense_account_id integer,
    account_journal_suspense_account_id integer,
    account_journal_early_pay_discount_gain_account_id integer,
    account_journal_early_pay_discount_loss_account_id integer,
    account_sale_tax_id integer,
    account_purchase_tax_id integer,
    account_purchase_receipt_fiscal_position_id integer,
    currency_exchange_journal_id integer,
    income_currency_exchange_account_id integer,
    expense_currency_exchange_account_id integer,
    incoterm_id integer,
    batch_payment_sequence_id integer,
    account_opening_move_id integer,
    account_default_pos_receivable_account_id integer,
    expense_accrual_account_id integer,
    revenue_accrual_account_id integer,
    automatic_entry_default_journal_id integer,
    domestic_fiscal_position_id integer,
    account_fiscal_country_id integer,
    tax_cash_basis_journal_id integer,
    account_cash_basis_base_account_id integer,
    account_discount_income_allocation_id integer,
    account_discount_expense_allocation_id integer,
    income_account_id integer,
    expense_account_id integer,
    price_difference_account_id integer,
    fiscalyear_last_month character varying NOT NULL,
    chart_template character varying,
    bank_account_code_prefix character varying,
    cash_account_code_prefix character varying,
    transfer_account_code_prefix character varying,
    tax_calculation_rounding_method character varying,
    terms_type character varying,
    quick_edit_mode character varying,
    account_price_include character varying NOT NULL,
    fiscalyear_lock_date date,
    tax_lock_date date,
    sale_lock_date date,
    purchase_lock_date date,
    hard_lock_date date,
    account_opening_date date,
    invoice_terms jsonb,
    invoice_terms_html jsonb,
    expects_chart_of_accounts boolean,
    anglo_saxon_accounting boolean,
    qr_code boolean,
    link_qr_code boolean,
    display_invoice_amount_total_words boolean,
    display_invoice_tax_company_currency boolean,
    account_use_credit_limit boolean,
    tax_exigibility boolean,
    account_storno boolean,
    restrictive_audit_trail boolean,
    autopost_bills boolean,
    internal_transit_location_id integer,
    stock_mail_confirmation_template_id integer,
    annual_inventory_day integer,
    annual_inventory_month character varying,
    stock_confirmation_type character varying,
    stock_move_email_validation boolean,
    stock_text_confirmation boolean,
    horizon_days double precision NOT NULL,
    account_stock_journal_id integer,
    account_stock_valuation_id integer,
    account_production_wip_account_id integer,
    account_production_wip_overhead_account_id integer,
    inventory_period character varying NOT NULL,
    inventory_valuation character varying,
    cost_method character varying NOT NULL,
    stock_sms_confirmation_template_id integer,
    has_received_warning_stock_sms boolean,
    quotation_validity_days integer,
    sale_discount_product_id integer,
    downpayment_account_id integer,
    sale_onboarding_payment_method character varying,
    portal_confirmation_sign boolean,
    portal_confirmation_pay boolean,
    prepayment_percent double precision,
    sale_order_template_id integer,
    security_lead double precision NOT NULL,
    additional_hours integer,
    CONSTRAINT res_company_check_quotation_validity_days CHECK ((quotation_validity_days >= 0))
);

CREATE SEQUENCE public.res_company_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_company_id_seq OWNED BY public.res_company.id;

CREATE TABLE public.res_country (
    id integer NOT NULL,
    address_view_id integer,
    currency_id integer,
    phone_code integer,
    create_uid integer,
    write_uid integer,
    code character varying(2) NOT NULL,
    name_position character varying,
    name jsonb NOT NULL,
    vat_label jsonb,
    address_format text,
    state_required boolean,
    zip_required boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.res_country_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_country_id_seq OWNED BY public.res_country.id;

CREATE TABLE public.res_country_state (
    id integer NOT NULL,
    country_id integer NOT NULL,
    create_uid integer,
    write_uid integer,
    name character varying NOT NULL,
    code character varying NOT NULL,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.res_country_state_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_country_state_id_seq OWNED BY public.res_country_state.id;

CREATE TABLE public.res_currency (
    id integer NOT NULL,
    name character varying NOT NULL,
    symbol character varying NOT NULL,
    iso_numeric integer,
    decimal_places integer,
    create_uid integer,
    write_uid integer,
    full_name character varying,
    "position" character varying,
    currency_unit_label jsonb,
    currency_subunit_label jsonb,
    rounding numeric,
    active boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    CONSTRAINT res_currency_rounding_gt_zero CHECK ((rounding > (0)::numeric))
);

CREATE SEQUENCE public.res_currency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_currency_id_seq OWNED BY public.res_currency.id;

CREATE TABLE public.res_partner (
    id integer NOT NULL,
    company_id integer,
    create_date timestamp without time zone,
    name character varying,
    parent_id integer,
    user_id integer,
    state_id integer,
    country_id integer,
    industry_id integer,
    color integer,
    commercial_partner_id integer,
    create_uid integer,
    write_uid integer,
    complete_name character varying,
    ref character varying,
    lang character varying,
    tz character varying,
    vat character varying,
    company_registry character varying,
    website character varying,
    function character varying,
    type character varying,
    street character varying,
    street2 character varying,
    zip character varying,
    city character varying,
    email character varying,
    phone character varying,
    commercial_company_name character varying,
    company_name character varying,
    properties jsonb,
    barcode jsonb,
    comment text,
    partner_latitude numeric,
    partner_longitude numeric,
    active boolean,
    employee boolean,
    is_company boolean,
    partner_share boolean,
    write_date timestamp without time zone,
    message_bounce integer,
    email_normalized character varying,
    signup_type character varying,
    phone_sanitized character varying,
    specific_property_product_pricelist jsonb,
    invoice_template_pdf_report_id integer,
    supplier_rank integer,
    customer_rank integer,
    autopost_bills character varying NOT NULL,
    credit_limit jsonb,
    property_account_payable_id jsonb,
    property_account_receivable_id jsonb,
    property_account_position_id jsonb,
    property_payment_term_id jsonb,
    property_supplier_payment_term_id jsonb,
    trust jsonb,
    ignore_abnormal_invoice_date jsonb,
    ignore_abnormal_invoice_amount jsonb,
    invoice_sending_method jsonb,
    invoice_edi_format_store jsonb,
    property_outbound_payment_method_line_id jsonb,
    property_inbound_payment_method_line_id jsonb,
    property_stock_customer jsonb,
    property_stock_supplier jsonb,
    picking_warn_msg text,
    global_location_number character varying,
    peppol_endpoint character varying,
    peppol_eas character varying,
    sale_warn_msg text,
    CONSTRAINT res_partner_check_name CHECK (((((type)::text = 'contact'::text) AND (name IS NOT NULL)) OR ((type)::text <> 'contact'::text)))
);

CREATE SEQUENCE public.res_partner_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_partner_id_seq OWNED BY public.res_partner.id;

CREATE TABLE public.res_users (
    id integer NOT NULL,
    company_id integer NOT NULL,
    partner_id integer NOT NULL,
    active boolean DEFAULT true,
    create_date timestamp without time zone,
    login character varying NOT NULL,
    password character varying,
    action_id integer,
    create_uid integer,
    write_uid integer,
    signature text,
    share boolean,
    write_date timestamp without time zone,
    totp_last_counter integer,
    totp_secret character varying,
    tour_enabled boolean,
    notification_type character varying NOT NULL,
    manual_im_status character varying,
    out_of_office_message text,
    out_of_office_from timestamp without time zone,
    out_of_office_to timestamp without time zone,
    odoobot_state character varying,
    odoobot_failed boolean,
    sale_team_id integer,
    property_warehouse_id jsonb,
    CONSTRAINT res_users_notification_type CHECK ((((notification_type)::text = 'email'::text) OR (NOT share)))
);

CREATE SEQUENCE public.res_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.res_users_id_seq OWNED BY public.res_users.id;

CREATE TABLE public.sale_order (
    id integer NOT NULL,
    campaign_id integer,
    source_id integer,
    medium_id integer,
    company_id integer NOT NULL,
    partner_id integer NOT NULL,
    pending_email_template_id integer,
    journal_id integer,
    partner_invoice_id integer NOT NULL,
    partner_shipping_id integer NOT NULL,
    fiscal_position_id integer,
    payment_term_id integer,
    preferred_payment_method_line_id integer,
    pricelist_id integer,
    currency_id integer,
    user_id integer,
    team_id integer,
    create_uid integer,
    write_uid integer,
    access_token character varying,
    name character varying NOT NULL,
    state character varying,
    client_order_ref character varying,
    origin character varying,
    reference character varying,
    signed_by character varying,
    invoice_status character varying,
    validity_date date,
    note text,
    currency_rate numeric,
    amount_untaxed numeric,
    amount_tax numeric,
    amount_total numeric,
    locked boolean,
    require_signature boolean,
    require_payment boolean,
    create_date timestamp without time zone,
    commitment_date timestamp without time zone,
    date_order timestamp without time zone NOT NULL,
    signed_on timestamp without time zone,
    write_date timestamp without time zone,
    prepayment_percent double precision,
    sale_order_template_id integer,
    incoterm integer,
    warehouse_id integer,
    incoterm_location character varying,
    picking_policy character varying NOT NULL,
    delivery_status character varying,
    effective_date timestamp without time zone,
    customizable_pdf_form_fields jsonb,
    project_id integer,
    CONSTRAINT sale_order_date_order_conditional_required CHECK (((((state)::text = 'sale'::text) AND (date_order IS NOT NULL)) OR ((state)::text <> 'sale'::text)))
);

CREATE SEQUENCE public.sale_order_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sale_order_id_seq OWNED BY public.sale_order.id;

CREATE TABLE public.sale_order_line (
    id integer NOT NULL,
    order_id integer NOT NULL,
    sequence integer,
    company_id integer,
    currency_id integer,
    order_partner_id integer,
    salesman_id integer,
    product_id integer,
    product_uom_id integer,
    linked_line_id integer,
    combo_item_id integer,
    create_uid integer,
    write_uid integer,
    state character varying,
    display_type character varying,
    virtual_id character varying,
    linked_virtual_id character varying,
    qty_delivered_method character varying,
    invoice_status character varying,
    analytic_distribution jsonb,
    extra_tax_data jsonb,
    name text NOT NULL,
    product_uom_qty numeric NOT NULL,
    price_unit numeric NOT NULL,
    discount numeric,
    price_subtotal numeric,
    price_total numeric,
    price_reduce_taxexcl numeric,
    price_reduce_taxinc numeric,
    qty_delivered numeric,
    qty_invoiced numeric,
    qty_to_invoice numeric,
    untaxed_amount_invoiced numeric,
    untaxed_amount_to_invoice numeric,
    is_downpayment boolean,
    is_expense boolean,
    collapse_prices boolean,
    collapse_composition boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    technical_price_unit double precision,
    price_tax double precision,
    customer_lead double precision NOT NULL,
    is_optional boolean,
    warehouse_id integer,
    is_service boolean,
    project_id integer,
    task_id integer,
    CONSTRAINT sale_order_line_accountable_required_fields CHECK (((display_type IS NOT NULL) OR is_downpayment OR ((product_id IS NOT NULL) AND (product_uom_id IS NOT NULL)))),
    CONSTRAINT sale_order_line_non_accountable_null_fields CHECK (((display_type IS NULL) OR ((product_id IS NULL) AND (price_unit = (0)::numeric) AND (product_uom_qty = (0)::numeric) AND (product_uom_id IS NULL) AND (customer_lead = (0)::double precision))))
);

CREATE SEQUENCE public.sale_order_line_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sale_order_line_id_seq OWNED BY public.sale_order_line.id;

CREATE TABLE public.sale_order_line_invoice_rel (
    invoice_line_id integer NOT NULL,
    order_line_id integer NOT NULL
);

CREATE TABLE public.stock_warehouse (
    id integer NOT NULL,
    company_id integer NOT NULL,
    partner_id integer,
    view_location_id integer NOT NULL,
    lot_stock_id integer NOT NULL,
    wh_input_stock_loc_id integer,
    wh_qc_stock_loc_id integer,
    wh_output_stock_loc_id integer,
    wh_pack_stock_loc_id integer,
    mto_pull_id integer,
    pick_type_id integer,
    pack_type_id integer,
    out_type_id integer,
    in_type_id integer,
    int_type_id integer,
    qc_type_id integer,
    store_type_id integer,
    xdock_type_id integer,
    reception_route_id integer,
    delivery_route_id integer,
    sequence integer,
    create_uid integer,
    write_uid integer,
    name character varying NOT NULL,
    code character varying(5) NOT NULL,
    reception_steps character varying NOT NULL,
    delivery_steps character varying NOT NULL,
    active boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone
);

CREATE SEQUENCE public.stock_warehouse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.stock_warehouse_id_seq OWNED BY public.stock_warehouse.id;

CREATE TABLE public.uom_uom (
    id integer NOT NULL,
    sequence integer,
    relative_uom_id integer,
    create_uid integer,
    write_uid integer,
    parent_path character varying,
    name jsonb NOT NULL,
    relative_factor numeric NOT NULL,
    factor numeric,
    active boolean,
    create_date timestamp without time zone,
    write_date timestamp without time zone,
    package_type_id integer,
    CONSTRAINT uom_uom_factor_gt_zero CHECK ((relative_factor <> (0)::numeric))
);

CREATE SEQUENCE public.uom_uom_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.uom_uom_id_seq OWNED BY public.uom_uom.id;

ALTER TABLE ONLY public.account_move ALTER COLUMN id SET DEFAULT nextval('public.account_move_id_seq'::regclass);

ALTER TABLE ONLY public.account_move_line ALTER COLUMN id SET DEFAULT nextval('public.account_move_line_id_seq'::regclass);

ALTER TABLE ONLY public.account_tax ALTER COLUMN id SET DEFAULT nextval('public.account_tax_id_seq'::regclass);

ALTER TABLE ONLY public.folio_room_line ALTER COLUMN id SET DEFAULT nextval('public.folio_room_line_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_floor ALTER COLUMN id SET DEFAULT nextval('public.hotel_floor_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_folio ALTER COLUMN id SET DEFAULT nextval('public.hotel_folio_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_folio_line ALTER COLUMN id SET DEFAULT nextval('public.hotel_folio_line_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_room ALTER COLUMN id SET DEFAULT nextval('public.hotel_room_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_room_amenities ALTER COLUMN id SET DEFAULT nextval('public.hotel_room_amenities_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_room_amenities_type ALTER COLUMN id SET DEFAULT nextval('public.hotel_room_amenities_type_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_room_type ALTER COLUMN id SET DEFAULT nextval('public.hotel_room_type_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_service_line ALTER COLUMN id SET DEFAULT nextval('public.hotel_service_line_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_service_type ALTER COLUMN id SET DEFAULT nextval('public.hotel_service_type_id_seq'::regclass);

ALTER TABLE ONLY public.hotel_services ALTER COLUMN id SET DEFAULT nextval('public.hotel_services_id_seq'::regclass);

ALTER TABLE ONLY public.ir_attachment ALTER COLUMN id SET DEFAULT nextval('public.ir_attachment_id_seq'::regclass);

ALTER TABLE ONLY public.ir_config_parameter ALTER COLUMN id SET DEFAULT nextval('public.ir_config_parameter_id_seq'::regclass);

ALTER TABLE ONLY public.ir_module_module ALTER COLUMN id SET DEFAULT nextval('public.ir_module_module_id_seq'::regclass);

ALTER TABLE ONLY public.product_category ALTER COLUMN id SET DEFAULT nextval('public.product_category_id_seq'::regclass);

ALTER TABLE ONLY public.product_pricelist ALTER COLUMN id SET DEFAULT nextval('public.product_pricelist_id_seq'::regclass);

ALTER TABLE ONLY public.product_product ALTER COLUMN id SET DEFAULT nextval('public.product_product_id_seq'::regclass);

ALTER TABLE ONLY public.product_template ALTER COLUMN id SET DEFAULT nextval('public.product_template_id_seq'::regclass);

ALTER TABLE ONLY public.res_company ALTER COLUMN id SET DEFAULT nextval('public.res_company_id_seq'::regclass);

ALTER TABLE ONLY public.res_country ALTER COLUMN id SET DEFAULT nextval('public.res_country_id_seq'::regclass);

ALTER TABLE ONLY public.res_country_state ALTER COLUMN id SET DEFAULT nextval('public.res_country_state_id_seq'::regclass);

ALTER TABLE ONLY public.res_currency ALTER COLUMN id SET DEFAULT nextval('public.res_currency_id_seq'::regclass);

ALTER TABLE ONLY public.res_partner ALTER COLUMN id SET DEFAULT nextval('public.res_partner_id_seq'::regclass);

ALTER TABLE ONLY public.res_users ALTER COLUMN id SET DEFAULT nextval('public.res_users_id_seq'::regclass);

ALTER TABLE ONLY public.sale_order ALTER COLUMN id SET DEFAULT nextval('public.sale_order_id_seq'::regclass);

ALTER TABLE ONLY public.sale_order_line ALTER COLUMN id SET DEFAULT nextval('public.sale_order_line_id_seq'::regclass);

ALTER TABLE ONLY public.stock_warehouse ALTER COLUMN id SET DEFAULT nextval('public.stock_warehouse_id_seq'::regclass);

ALTER TABLE ONLY public.uom_uom ALTER COLUMN id SET DEFAULT nextval('public.uom_uom_id_seq'::regclass);

INSERT INTO public.account_move VALUES
	(1, 1, NULL, 1, 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 7, 7, 7, NULL, 2, NULL, 1, NULL, 1, NULL, NULL, 1, 1, 'INV/2026/', NULL, 'INV/2026/00001', 'S00002', 'posted', 'out_invoice', 'no', NULL, 'INV/2026/00001', NULL, 'not_paid', NULL, 'Fixture Invoiced Guest', 'S00002', NULL, '2026-11-25', NULL, '2026-11-25', '2026-11-25', NULL, NULL, NULL, NULL, 1.0, 230.00, 27.60, 257.60, 257.60, 230.00, 230.00, 27.60, 257.60, 257.60, 257.60, NULL, false, true, true, NULL, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, 1);

INSERT INTO public.account_move_line VALUES
	(3, 1, 1, 1, 1, 10000, 26, 1, 7, NULL, NULL, NULL, NULL, NULL, 6, 1, 22, NULL, NULL, NULL, 1, 1, 'INV/2026/00001', 'posted', 'S00002', 'Fixture VAT 12%', NULL, 'tax', '2026-11-25', '2026-11-25', NULL, NULL, NULL, NULL, 0.00, 27.60, -27.60, -27.60, -230.00, 0.00, 0.00, 0.00, 0.0, 0.00, 0.00, 0.00, NULL, NULL, false, NULL, false, NULL, NULL, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 100, NULL, NULL),
	(1, 1, 1, 1, 1, 0, 26, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 7, 1, 1, 1, 'INV/2026/00001', 'posted', 'S00002', 'FX-101', NULL, 'product', '2026-11-25', '2026-11-25', NULL, NULL, NULL, NULL, 0.00, 200.00, -200.00, -200.00, NULL, 0.00, 0.00, 2.00, 100.0, 200.00, 224.00, 0.00, NULL, NULL, false, NULL, false, false, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 100, NULL, false),
	(2, 1, 1, 1, 1, 1, 26, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 6, 1, 1, 1, 'INV/2026/00001', 'posted', 'S00002', 'Fixture Breakfast', NULL, 'product', '2026-11-25', '2026-11-25', NULL, NULL, NULL, NULL, 0.00, 30.00, -30.00, -30.00, NULL, 0.00, 0.00, 2.00, 15.0, 30.00, 33.60, 0.00, NULL, NULL, false, NULL, false, false, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 100, NULL, false),
	(4, 1, 1, 1, 1, 12000, 5, 1, 7, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, 1, 'INV/2026/00001', 'posted', 'S00002', 'S00002 - INV/2026/00001', NULL, 'payment_term', '2026-11-25', '2026-11-25', '2026-11-25', NULL, NULL, NULL, 257.60, 0.00, 257.60, 257.60, NULL, 257.60, 257.60, 0.00, 0.0, 0.00, 0.00, 0.00, 0.00, 0.00, false, NULL, false, NULL, NULL, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 100, NULL, NULL);

INSERT INTO public.account_tax VALUES
	(1, 1, 1, 1, NULL, 233, 1, 1, 'sale', NULL, 'percent', NULL, 'on_invoice', '{"en_US": "15%"}', NULL, NULL, NULL, 15.0000, true, true, false, true, NULL, '2026-11-25 07:59:36.995365', '2026-11-25 07:59:36.995365', NULL, NULL),
	(2, 1, 1, 1, NULL, 233, 1, 1, 'purchase', NULL, 'percent', NULL, 'on_invoice', '{"en_US": "15%"}', NULL, NULL, NULL, 15.0000, true, true, false, true, NULL, '2026-11-25 07:59:36.995365', '2026-11-25 07:59:36.995365', NULL, NULL),
	(3, 1, 1, 2, NULL, 233, 1, 1, 'sale', NULL, 'percent', NULL, 'on_invoice', '{"en_US": "0% Exports"}', NULL, NULL, NULL, 0.0000, false, true, false, true, NULL, '2026-11-25 07:59:36.995365', '2026-11-25 07:59:36.995365', NULL, NULL),
	(4, 1, 1, 2, NULL, 233, 1, 1, 'purchase', NULL, 'percent', NULL, 'on_invoice', '{"en_US": "0% Imports"}', NULL, NULL, NULL, 0.0000, false, true, false, true, NULL, '2026-11-25 07:59:36.995365', '2026-11-25 07:59:36.995365', NULL, NULL),
	(6, 1, 1, 1, NULL, 233, 1, 1, 'sale', NULL, 'percent', NULL, 'on_invoice', '{"en_US": "Fixture VAT 12%"}', NULL, NULL, NULL, 12.0000, true, true, false, true, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL);

INSERT INTO public.account_tax_sale_order_line_rel VALUES
	(2, 6),
	(3, 6),
	(4, 6),
	(5, 6);

INSERT INTO public.folio_room_line VALUES
	(1, 3, 2, 1, 1, '2026-11-30 07:59:57', '2026-12-02 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673'),
	(2, 4, 3, 1, 1, '2026-12-10 07:59:57', '2026-12-12 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_floor VALUES
	(2, 1, 1, 1, 'Fixture First Floor', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_folio VALUES
	(2, 2, NULL, 1, 1, 'Folio/00002', 'manual', '2026-11-30 07:59:57', '2026-12-02 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL),
	(3, 3, NULL, 1, 1, 'Folio/00003', 'manual', '2026-12-10 07:59:57', '2026-12-12 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL);

INSERT INTO public.hotel_folio_line VALUES
	(2, 2, 2, 1, 1, NULL, '2026-11-30 07:59:57', '2026-12-02 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673'),
	(3, 4, 3, 1, 1, NULL, '2026-12-10 07:59:57', '2026-12-12 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_room VALUES
	(3, 7, 2, 2, 1, 2, 2, NULL, 1, 1, 'occupied', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673'),
	(4, 8, 2, 2, 1, 2, 2, NULL, 1, 1, 'occupied', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_room_amenities VALUES
	(2, 5, 2, NULL, 1, 1, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_room_amenities_type VALUES
	(2, NULL, 8, 1, 1, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_room_hotel_room_amenities_rel VALUES
	(3, 2),
	(4, 2);

INSERT INTO public.hotel_room_type VALUES
	(2, NULL, 7, 1, 1, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_service_line VALUES
	(1, 3, 2, 1, 1, '2026-11-30 07:59:57', '2026-12-02 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673'),
	(2, 5, 3, 1, 1, '2026-12-10 07:59:57', '2026-12-12 07:59:57', '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_service_type VALUES
	(2, NULL, 9, 1, 1, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.hotel_services VALUES
	(2, 6, 2, NULL, 1, 1, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.ir_config_parameter VALUES
	(2, 1, 1, 'database.uuid', 'f1a7c0de-0019-4000-8000-000000000019', '2026-11-25 07:58:14.610285', '2026-11-25 07:58:14.610285');

INSERT INTO public.ir_module_module VALUES
	(36, NULL, NULL, '2026-11-25 07:58:26.177026', 1, NULL, NULL, 'base', 'Odoo S.A.', '/base/static/description/icon.png', 'installed', '19.0.1.3', '{"en_US": "Base"}', 4, NULL, false, false, false, 'LGPL-3', 100, true, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'official', NULL),
	(84, NULL, NULL, '2026-11-25 07:59:35.247195', 1, NULL, NULL, 'hotel', 'Odoo Community Association (OCA),
                Serpent Consulting Services Pvt. Ltd.', '/hotel/static/description/icon.png', 'installed', '19.0.1.0.0', '{"en_US": "Hotel Management"}', 23, NULL, true, false, false, 'LGPL-3', 100, false, false, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'official', NULL);

INSERT INTO public.product_category VALUES
	(1, NULL, 1, 1, 'Goods', 'Goods', '1/', NULL, '2026-11-25 07:58:43.908252', '2026-11-25 07:58:43.908252', NULL, NULL, NULL, 'partial', NULL, '{"1": "standard"}', NULL, NULL, NULL),
	(2, NULL, 1, 1, 'Expenses', 'Expenses', '2/', NULL, '2026-11-25 07:58:43.908252', '2026-11-25 07:58:43.908252', NULL, NULL, NULL, 'partial', NULL, '{"1": "standard"}', NULL, NULL, NULL),
	(3, NULL, 1, 1, 'Services', 'Services', '3/', NULL, '2026-11-25 07:58:43.908252', '2026-11-25 07:58:43.908252', NULL, NULL, NULL, 'partial', NULL, '{"1": "standard"}', NULL, NULL, NULL),
	(7, NULL, 1, 1, 'Fixture Suite', 'Fixture Suite', '7/', NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, 'partial', NULL, NULL, NULL, NULL, NULL),
	(8, NULL, 1, 1, 'Fixture Comfort', 'Fixture Comfort', '8/', NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, 'partial', NULL, NULL, NULL, NULL, NULL),
	(9, NULL, 1, 1, 'Fixture Dining', 'Fixture Dining', '9/', NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, 'partial', NULL, NULL, NULL, NULL, NULL);

INSERT INTO public.product_pricelist VALUES
	(2, 16, 1, 1, 1, 1, '{"en_US": "Fixture Pricelist"}', true, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673');

INSERT INTO public.product_product VALUES
	(5, 5, 1, 1, NULL, NULL, '', NULL, NULL, NULL, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, NULL),
	(6, 6, 1, 1, NULL, NULL, '', NULL, NULL, NULL, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, NULL, NULL),
	(7, 7, 1, 1, NULL, NULL, '', NULL, NULL, NULL, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, false, NULL, NULL),
	(8, 8, 1, 1, NULL, NULL, '', NULL, NULL, NULL, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, false, NULL, NULL);

INSERT INTO public.product_supplier_taxes_rel VALUES
	(5, 2),
	(6, 2),
	(7, 2),
	(8, 2);

INSERT INTO public.product_taxes_rel VALUES
	(5, 1),
	(6, 6),
	(7, 6),
	(8, 6);

INSERT INTO public.product_template VALUES
	(5, 1, 8, 1, NULL, NULL, 1, 1, 'consu', 'no', NULL, '{"en_US": "Fixture Minibar"}', NULL, NULL, NULL, NULL, 1.0, 0.00, 0.00, true, true, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, 0, 14, 'none', NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, 'manual', 'no', 'order', NULL, NULL, NULL, NULL),
	(6, 1, 9, 1, NULL, NULL, 1, 1, 'consu', 'no', NULL, '{"en_US": "Fixture Breakfast"}', NULL, NULL, NULL, NULL, 15.0, 0.00, 0.00, true, true, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, 0, 14, 'none', NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, 'manual', 'no', 'order', NULL, NULL, NULL, NULL),
	(7, 1, 7, 1, NULL, 2, 1, 1, 'consu', 'no', NULL, '{"en_US": "FX-101"}', NULL, NULL, NULL, NULL, 100.0, 0.00, 0.00, true, true, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, 0, 14, 'none', NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, 'manual', 'no', 'order', NULL, NULL, NULL, NULL),
	(8, 1, 7, 1, NULL, 2, 1, 1, 'consu', 'no', NULL, '{"en_US": "FX-102"}', NULL, NULL, NULL, NULL, 140.0, 0.00, 0.00, true, true, true, false, false, NULL, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', NULL, NULL, 0, 14, 'none', NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, 'manual', 'no', 'order', NULL, NULL, NULL, NULL);

INSERT INTO public.res_company VALUES
	(1, 'My Company', 1, 1, NULL, '2026-11-25 07:58:14.610285', '1/', NULL, 1, NULL, NULL, 1, NULL, '', 'Lato', NULL, NULL, 'Blank', NULL, NULL, NULL, true, true, '2026-11-25 07:59:36.995365', '\x6956424f5277304b47676f414141414e5355684555674141414c514141414177434159414141433437464438414141666b456c455156523432745639655a5255316258336235397a68787036486d6c6f415673454c49526757685448526756466a54696c5347496d6f39456b6d766465346b7679586f61585372313861795676765a65566c3377766d70414a5938416c7052676a47715948564b4b474544764767585a6961756d6d3657366736614747652b385a766a2b36437175624271717170655737613955436d6a35317a396e37642f62353758333232596344384148516d55382b6a7748414173417a2f3836336e5a6e545475585a686a4a745441437377485a327068304b614d637a3759787879435466646a524b4a6f573079387145436867627937537a6970424a396e316e504536796770514664444b72624646414f7a4e48615636424375655a39346769326f6e4d4a312f46475a6e325868457951655a64716b695a71447a486c6e32664b6d42734c476343544b524d4a68496e444941796975796b56344469636858676e6d5977733879377867506d5168544133775046465373547277435a5a4d45734335534a6d544e527a335363434143436e3259725a4752655745776e7378536a6b4a6c715a64706c4656344d6d417456654b474b4d334d55586f684d6a4a786c324333514d724d437763787971456b684d6e6b2f63534941614b4d416853507a7374506453574f6359425946674a6d4e736b4b6e473878474561734f7872444d4b464468587046674c6f526d6e4245344d517159635956616f554b585268706e75304956783473453833686c6f677577586d5035413458536a474b6f56364667506d4e775970774759702f4c685534336d4e6b4567336b305a7936555a716743486342697745796a4f4c4e587045784f74774e34576e4269354d6d465a42474b4f39334f5471356c4c675355624e54594367477a5653416f3379755a6943496d654b45794765397164556267684534785577766c517355344f385536674e6e4246637350692b484d6863686b74434e587a45517442737855424a694c3563786e4845364d6b335379474334304554516a3177453855384763625a664c6d536369396a35657931774d6d4d386f6e504178764d31437542417462467a6f64327a48544361546368794b4b34517a573055364f2b4d4238336843633856736d68546b414459324e767238666a2b7671616c52313135377257787261394d46794b5359545a4e4363544b3633576b7a656a51474679706b536333646571585454444e4f7767393164696a364a4b416b6f466b4172626c67316e6b6f5842646f6d5366536a386a36412f6e4770636537576857446b2f484b7043436355444764314e424549495361516d646450767661534d4962656d5056706c2f38703961616945696652707052714f65654f776e6330387750637a6e7a52506752575444624e31353863334f4a763449445146716d55302f393662472f6e4753732f7a3978356f4a7859685154686c71455258596b456e4766577631555a64415876437370456e2b505243492f694d5669787978324a4249357a75466375584b6c6c55366e6558643374346478624a6f73573761736445704a79456832646d6c5042716938484e6878634d64516132757264774a36346f5858414455506636477976783949384b53754c3630322b6737745438533278314c764d57645745304339736a4952776671677636616934596c796630555651426849396830454d414e41596f78566b343369766f5743756442775a5a5a6d544e522b684656552f44434f75427550786c565451314e66796b304a6148556f476f324f474751304768327245326b41694344436f6f6a71484d716a38346b7a687848574d6351673032796d564b6b4e676449614a725141597859503154533374714a31535351533064466f4e4373554e44633369396257567546622b646e664d364f3070615463455255555a49354f482b6b583769494148546c394741396e4c6d6254784544786d79594d6744527377774d6834516d76416943414b48474b475070454a52704e4a4a697a71785552386b2f4c7a484c6d796b39662b3458666c50724b616833587352696e4479696c42686c345738414f386f364258512f62504e42655531722f62306b6e4b556d4441356f3053484e75734636763831655072332f3077556845733269554b514c773763693347614a4146434d6d78576a4f374146414f4c794778324c4c355233583350584432724a4a583071374b524149706d6d694d3758764d327333504c61797672342b324e33644c57664d6d4b46333764726c334c34342f4c4747594e4e714954316f4464695768514e44375a392f664e4f6a50777548777a775769386e3349633663425571786955594b6746732b74627a79317650756544566742616341684b51377448666c686f666d6a724c513777566e396959497a4d5836566752414767557154694d494c726d33514a75796c704547424945627246517937324a74436e676b742f6b454f615a684c7a41384634797859664f6e415561454771756865646b314878364b52756b524149594731476a72506b595936686956694d57577130676b776c5a756933373936745239317757736b746c4375454a4b5a5653776d76387a663862385a317a4c37612b75726b61344c537a577a6c3162576561722b5a355753696d6c684733367243504a336a2b4d41655a434c54506c574c324a326b677969677a4e76562b3547524f5a39694141654559426e5279654f516b63365750374c6a74712b62677a3445773978353637506945472f337134624f2b646a50474b6779556448624f536c34526431354643535545716b39476e695451304f4f4f387a6d72343956314c372f3861514f44456f5569386339445a3938566e2f76655a5057474565517978334b5652484f655441745165522f72775651632f62357654746845784a70516e532b79794b65644f447a305132377a363635467778497132526456484a6e2f696d3256473562536b6d7841474d3432554742726f5472357a50344551436f5830364a68714f42796d55452f496d464d33522b2f7332556e62734133786546794e5575677843397651304543544a3039575455314e4c42514c36564772444d4c683849694d786c67736c7558617371576c5264585631544541434956434f6a4f784b64495334585071357567595973684d4f426f567276517739716259695a6269592f48696c705957597845574954752b74726f3248597646314367416a5a5543537546776d49563651675141327744453431475a5851484334544339394e4a4c787544676f4e48643353314f4d4d4750665566322f657547316c46726179764479437a4a51674d46783342435263793459776f4c4e59536d586e3352683971504a767332374476382b6a64445a313277326f4f726d544c724447575751304d7a786e676d4d674b74744e54516a42456a67772f4c57576b4e762b314854374c7a795565652f6556746a59324e2f6f364f4475415557584e5a367647784a5a2f366356334a6c4839494f6b6c684d4a4f35326b6e75476e727a676d337844627576762f4c362b56504c5a6d356e326a5155704c4a4e322b684b7648502f34357365665444542f746a4b30397a63724559356c574f394c3674344d7964636c712f46797a342b6e4341464e4f4e6271464d3578626c6830704e516a6953475439384167416948312b6859624c6b383866694f5736324f576652494a4d4c4757455648747a7670633472663434324e4336324f6a75314f4161766a6d4e6d5652703567486a467a49693052413475674e6a322b7964525364784f6f4f30426c5a5146574e744d564c705353344977444448413878324845504b6c6b49474148754363384b4b57304b31773933444f536a70746d515a524e417741705a5862476e5451306c365565713161742b7459564d356463487a524b7a3347464b3071736b704a70397654764575686a6e777a632b774d66443170704e2b6e36624c39314a4e32373966464e6a7a36344a7279474c3438747a31705a33644c5349755078754144416c79315a646c6b7071372f41533666725447346c70656e746562332f35542f47597373374d362b327334494d68554c6c6b36736d583841735377486163464b694b2f376e5461396c7752594f672f66314c4c3745494d4d575568754f53487037392f2f707a78306438454b686b44577059744c466c6d565a576d76535369656a6634712b4d487632374f6f4c7031353575314c69374a51593276666b746a557255647832396f6763373168734f5a706e4e7a664d4f476657356159626e4f473636524b2f50396a62703370652f76334774632f46596a45764641705a625731744c4e63427a41477a38644872506e574449617835556d746d42505465747134584e7364697361354c4c377830567341666d414641434931307838463932336674327555636d366a44337947506b3639687052306b32312f706266335457363973333576546435576e55337a63436d34557734576938616841484a67326256706e6c586a39707253525467664b4b69353068614f46464d49305454506c4a66634f7076712b74362f6a37625537337468785a50486c4e357862727962644665526c587a613561516b7051455145445130433135414b41494c42594c35785a7231753354706a31363564412b644f4f752f4c3036764f665a71424d5563343275612b6d38505833764754674247384b6931537975416d54346e6b554539712f333045776e2f452f6f4e6c64306d626d3574565042345874312f316b6475714176582f786f6a507430776238414d4567745143467870583970312f66664d6a7a37583962365339765832777672376531393364375456556e6a567665766e4d7a61514a50737550772b7a516b77427569375245654451654655656e7a764e4e635a7565394d755347684351776d4350504b396e52736576337453653664564f4c6d6c36707351714c6557635979673939484c4c677059375a39544f57787577676d646233454a5073724d443156694e7730686d39484471705667663435564f316841314c6f532f7066547566772b594a58655a686c6c6c6d435a3055494e413845732f37763751463138646349393850375a783965724d436a6e434d69397475576e68354e4b70442f6c35594c3742544769744962584167696c4c443030762b2b413348433831362b796157662f7365673653336c436974364c7250414437416242494a494a6f4e4b724356332f303167702f336266486b7538567670712b425764642f73694c7535372f31707476766a6c346b6b32365532377873324938397767694441447179732b61576f584a4736617957532f55426963394a4b54514672664d7445793874694d64767953326566585071365a5654627674317474754f61494f44713365384f742f37657276754555706d57534d363246584d614d4854515141482f2f34782f50654e476c746265587a367563462f2f4463302b754f4f6b642b62746b3256306f707867782f6e612f7876737952546d30594a7539334433316e59337a6a472b664d4f4d6475525773577a4c4b317464554c332f4352723953584e543568632f39384b456a50636157554171357749447a68576d525631766f612f72466c39744b744330494c61712b3838736f30414243524a6e444e796651597544615a4f614c76626b71517751795877445670726a6b7a584e50484e51417778725442544a6542613631494738776f6e56593136374553712b78737a334d68704143424461436b49456375522f455245596c455250506935764b72617a2b3773625a6b306c634d5a6c524a543771753530424b41646431704a4a612b466c676272322f6364587456332f737578306448616c494a4b4c44345443505271507168705962356b38706d62362b684a664f4635346e553237536354784861365668614c756d4b6c43376f7161302f714f6535796b2b4c4175584d5a5a6479566b30476c584c622f7a6f50396557546c6c374d766e573251332f75504473526473756e3339357259592b687245543049775472754473464848486b784a305133466d6b622f637834496c70725a7349675a584f364a33734f4d7a723231357266754f4f2b35346250723036613331395a505758686936384b337762654576726e762b695438636358742f61426f476733353361534569565944436a6d3051764e4c396968754a614859672f644c584270332b64797a44346c6f7235516c58515774706d7a342b6b447179666333477a682b46516d4672313635644c4d4f5a5a577472713766736d747357567874542f6c4d4c6b6f354943394d307555754f546a694a50593549487a4a4e30394a61492b6b4d755657426d766b7a7035322f49754e455a61636961536a53304b53684351446d314d3352414843304d32466f725269676166677a306d66523041516945744b447763326d636e2f567a495133674c5249376b3036513373636d5235414541714650353757333948526146544e346e502f70387173767a7a704a46796c6c545a4d77307172314a476b6b396a74777447326152757563495551516b3471612f7a57725576447430616a555a56782f6e694e37367948676d5a706564704c6579426974756d7a5065556b457537513370524d774f592b2b486c7769745343514342415565354b7675796132785a5838636e2f4e554b2b63444261766f6e306b467670722f6e6739495a7a66304848753361354f64346e5455686a4a77437a7a48386258416d7068565a51776a4a4d356b726e62372b502f2f3746634468386630314e7a58494155696b704c4e734b6c7061582f6d6a4a6b69764f5074527a344b47306d784c45474d2f2f464e4b5963556350674e665774707a69385a6550396f6e752b3458324642454252455445794a5870524f3951782b6542754468382b49395a436956656650464641594171724b71495252616b3971545039426b4a5a334262682f663268513976664f6744667a6d386257353338734144697054446942744a4e796e4b7a657162506e54357a56646e4a7547595a7a4a333975776b414e775a386e6965356c5278346a715248747a664b7a715872747a2b302b61662f2b4848462b7738384e49746144756d504a326e6264616f68695969766653614479306f73636f2f6b585a53676f674d496f612b5a4f383358753766506e666c786f632b73442b783734492b352f417a6c6d455a556b764e4e4e4e6c756a714b454b786f50437075767537324b344a32634b486a70695152475977784f707a712b652f647956317a483337687077733633583158444b6d2b485a7734534939686b5051492b53716636544f473067507866656e584c38724b747a66522b53575a493938797333725a6a53323374305152565a6b49555462736d4e66425a7a59475a79346b4732705972634d624e434169704654697255676b776f4c42306d7530316b4a72725141597275734b6e393948566257544c396e7938705a4f7a56552f41344f6d676841394f74744f5a6b4a68636b313444662f647869665770647a554d375a704d326a745771624e4270796a5033336d2b5764656e6c632f4c35674a4a336b52524451523655756272326f7934622f594559376d7a4c5153597544676e77382f3965474e477a652b544552446258397436346c742b7530502b37322b4279335459744351426a4e3164556e394c5144417552347a5372547572585557414737364441565158754d6a42756f6533503950543231597536463552764d5167494858586e75742b31524752516e467369744439716c5577336f74522f574e5068364167704b6d5962462b722f6358717a65742f4e354c4c3778304942774f707a66466e336e7474322f3934754d706d57673375575734776c552b7778634b4e3335364c6741455a4d6d314a7265314a69307377364a425a2b444a3152742b39655634664d4d374d775a6e444b3366764f36357664317633757a434f63675a5a7a7244494331544d6742592b4d475763334c6b61777835417a33787a72556632624a6c79393879386a3334324f5a565030724b2f7638375172372b366c73426f484a505a634535336979484d78643655424765634563346c566f44706d6c5752614e524a5431765032504d55456f70726256676a476d744e66556636652b635654327246416f2b6e5766634d4a384d735a30394f306c446b342f374f346749424767696743757a55304f5455434a7230565662754930416f4c51696344626e7a4e526153394d7734626e792b54662b657544777666662b7a4e526157395856316346774f4d775070512f2b50693153494d7273656b71614467416b523449314336795553444541737254654c2b675551395261677a4f444a357a456f5a64372f72596a4841377a31745a576c624d7a65394a48657449632f624f2b724a4667616f62574771534a74465a494a314a72772b45776e7a5a746d69385769316d7a5a7330717852373044346d424c515933414b326c795333754a62787047544c56704a556d3069436c466671474471324d5243497346416f46646d475864322f7a76576238722f47446732376642734d774b6573524b575554414652552b4a73345a3661476c715a686b75654a352f612b31744d6469577731744e6255334e787368734e6833705075666a6f74556d4245772f524d736d6b5a4f6d6d67774950504445556b58626468474242435370366a5453615667453848466c78303055566c76516436667a77774d4e415444415a743237594e76393976397666336231792f666e32386165377347797a7543306f6c46444c4f5941475a5869656371515453476d7145677155534e6f48306e4e6f3578314d6f41676349325178425273776c45463535397463474147355a6c67514172725372316274695564414d414f536f7a454b744e4e665156476158535143712b6342486958753254304f64464a6e454346446f3733693759794154713831474e505170644d637a5559305430512b65773046424941454179575453414b446e38586d4f317071306642637347674452734634315a5856446c447468703036644f6f7954357177385472683263774b42394c43634f484748514d4332625143676d357161464143514545497266657a376c565963414a4a65737542645559615236593535426256335949634a414a7978584b654f70425453623562554e6c576339373331573966766675667464793770367a7636594371522b6c3133562f63335636396576585471334b6d566453583133325a676f507957593561765135447069523470314f452b686d70443732344944653851496e476f66372b5355674977704251676a6f733074483937782f5a3051304d44335454354f31347346704d3176736b7466697349614169414e4f506f4241426e4b4a465353696f4154476b4654586f4b6766523135337a504136423339473272306c6f46744e62365a463549646a494253464a2b613959786d5443546561506c574a5564753051374d644b6174474c457757787a635377576b314f4e7161713575566e47326d4975456148454c4c31434b674741754e53654e6f4b735978686f72494d78706a56424d57496f72796a2f524451615665765872336549534b395973634a62734b426c55706c56635a3051336a4854784a696a4161442f63482b586c464b436875554c70692f573047593048685868634a694873515a6a7974665158514251366173737544424f556164755862674d41417a44457054626a6f69356e714d713764723737726a754c72647a2f2b352f2b38317a44392b662f65386c6c79365a33314231396b394b575558494661346d4967353930704255735565453368306c343865316955616a576b5054386e507054533978667075504238353352466f4572624a7a506e37395a783538592f637258323139712f585169713750345a596c74313866744d752b35673176424847704252314a6454384c414a37482b68695949434c4c45363471395a5664635033567479364a62726c71453662423131513937527557615675653845516d566666646c554e4968754b65455834454e3438663335484d6e77354c622f53452b793845346b4a3675697051632f394e5639332b38744e626e33674d5856424e5455336c433264642b56322f57584b654a7831686370734e65663137642b37662f436f414b4f357445394a376744514d56376936677456382b424e4c372f3742776348324832312b66764f52705974764f722f656e767a664e766b6d75644b56426a6547633749643067426f7439373939726d592b37715042304b4f534d735375377a706b7a66652f64416275312f356c316773646a6747476c4f2b50554d484e674a413355563148746f4c7937597a696b6b677357437058413659303534415455704a566532722f5a4a766575426a6a644f622f757734626d2b705654616277376a5978774b574b394b4b694c456337716e4873457a464a745563372f5750595261586835667a57417779664f334139387439356175343546703472717930367536633333544a6452664d764853506b7271554d7a62504a417565384e79414862434f70412f74324e503739724d416f63787664796c53523031516a64414b444e7963346d7438387535627674437130706a6b5934475a536d6f412b72686f682b666d6e55647a4d706d4d2f527942496843653342546239736b6237746c53626464646e55675075515933537159457036322b612b6c3958326347473951535a2f6b732f316d6563425742613234776c6b774e2f466462572b2f516d7641617676796c3552732f325854504b35582b6d6e6c704c2b55704b4b5053562f754153623537506e33747562324777632f323877423530674e6f3242386a55485a735a76637233596e45704948766c2f73726673736c6c384a7a5a626c5a632f6538365266663849455a433865576236713339665839723633543045537876454b3549337772566b773256447675644148415a2f68546e48474c68694d64476434335044746434516f66393964586d2f573354433664656b2b4a565861467953334c6b36346759746d644945314579694344484a34576f35595071786a4c724a57436868596145427061354d61365279554a795167694c4c5a783965704441373072664a62665a4d7a6772756534706d4533324d78336d632f777a325067516b6f704133625147704c3942377259336a766232747263652b2b397831792f592f31415176552f343750394445536556454a774d6f4f324c4c6d79784b36594b5348674b586541774d56776e37547730704979686f43512b5a6d4746675174437152654f544c4a2f5a353338366f4a55416348393331324d4e33664876435657464a4a7062583266475a77727333386c31726350737354777548456d632f326d623375775564696d34657a454c2b363436736d6473487253757a2f5846494d3966744d76366d31316f376e4f44617a53344a32734d6e48417551704430704c6b577551704a4163674e6653306d49387676485256596348442f3030482f6b4f7976367544757a2b64487437653572776e58794f394932653449495643756268686c4556695554596f6c735776705077426e3844306c416b4f556a5473512f5468744175556a4b466c4a654149394f516b414454527537764b564b6d49394c7559504c6f547746673362703175576d4c65547345322f5a747937597039317342772b4a6d6964384b4749414f6e71684e464645645173686176666c583933556d396e33646f33535062666b73693573674d44444734444e39426e48775075665168726454727933612f4f7a6d313445775837466942514e433170346a62333737634b4b3331572f3762647630475a5a6877754163726b37705876484f767961397762664b4175576d7a2f515a424b6f39306a356f355469787458347259506974674b474a61764945383469454b4b303036647a764157714848516d4e387843794e7631703037366442313963334364366677656d6d573336544d3459434177474e2b457a626475443133647761482f6b3057645733686c42424c46596a4c573374364f78736448652f507a36375231442b35594f75514e2f595a7778762b577a4c644d697a6a6b3853716536427a752b4c715238316554445551344672615357486741646a3864564242473261744d76763943563350653155386e3339594758727436365965744f494d4b41714d71484d343832656c51346d48507078664466463763735865697a6a45717475527132506f7145454962576d6a6a6e6b6e506a68425a576b57534a517750372f766a53483139483861637165414d6137433530756663732f59664c417236536d5936586c4c595a3450314468376576334c7a6931524e6b736d57322b47636f594a637a2b34725a4452665943323955576a567a6d39564c49644d576647386b76503574613765752b574e4f316c69754d2b3067684a4937476a397a68344b2b684c677567364339536570622b39544770313734314858334c43757a4b2b7339346245452b70302f3748377169634e76486b374d6d7a665050332f4b5a626558734b444e4f45504b545237393566722f6558774d71335279366a554439716562507666686f4b38304144416b334d5467772b742f6b763065733647686758563164535542344b62464e793073513930316b72775173356c667074516867396c2f662b5049333961317472612b5179426f3642475655567461576e676d6351764c7272747463616d717573427a6e5772444d727137784c364e5737647533586e6e64666674446c6a424a6b416a365359365632352f36487a30342b6937474e45456b42354c766c796262772b4b76766a5457352f636b7050496c412b5943385a4a64752f636e2b4f456e4c616e425331474a7258536835486c46664c78626e325a4c4c684332706d5a646c596d6e356566664564553037446c674a58543771524749524b4a6e436931674172677a4f4f564363745962447056656d654f544f7a634f5067316c31797a594e363865574f756445735758582f5a50522f364a2b397a4e7a776776726a73612b6f7a4e393733346c6a764b30432b3435494a6e634979353355634a74765a5058763273414d484470684343425949424d524646313255567a43384a395a446363534c4b63393133496e3163446a4d73306e6f41494246593536494f5647744f57707069664437362b626f6e614764757132746a5549396f64776b2b424f7556693074455635584e306548516a76316e4c59356c45334f623235754e72304f7a334b4577784c2b537448527354326462646653456a45575a536e543845454363594a6f786b6e7a726e4f2f5a31586e582f69755865734a593577427a4d716d4c64505074725935464f725a536446345647486b365273766d7957335a4d6d53733665614d397545556d385036454e66627a327738595633587533765179314b62706937624d466b65396f4b322f5450384954722b69792f315a33712b4f466a47783535494a4f694f377250724b556c776859422b4f5875583571653537485a76746d79377149364c352b63617552786c49774b70426e354a6c3058576a68785050575a433432436a4c64796672465651497370767a43653277534b50516a724156435253495246313058354a2b727565627243724c704f615155464163644c377a584a5075497074355162624b624e2f5843464b77786d4d454775366b793950752f5a7a5a746650776c3147452b427a565069684e35444d4f6657592f4e4f4d79694c7252492f305556674a724c57584c4646594936727a397a53306d4c4534334678383158684f3571715a36357930673645466f4930616336356d615847556b6d6874595a705741596a777348426a692f4674717a3630556e41664e7078776f756c475365777a424e644a4c43594b77384b4c555831586852636c4763346d45644d31506232646732417a703357314f56704d63415a503864675a7056742b54694277496a41694d50674a744e4d4d512f4f322f314452372f79324a62662f43776344764d4848337851765638346f6665515a67675558347634644a6169476e3352546a48316d5364434a7356576554727471315674714c626b69736d4c7279786c6c65636c336637704d46436d4a4b5838687457524d684a2f66364c7a7361313442596c54574f594a77306d7830597a7331576c2b6e507073346f6d3831454c61465273464d544e39744173636d7a6c4f6d5a67465269587349735a577245794d484a6d634c4c4a417034704f354248466d464363354d366338537970703973796a7935464e56454f344868756d7972454d702f705257425959324f6a485577466a55702f70546a726b6764634141696475417a432b345954777276483669657950764e4546516b734f4d63623735364f794a37617958647375626d37736f684a4d42476365627856514173746d547a684f44456d714a506a7662396a764a7935454441583672534d74396a346547764e46564e7366467858703533424f4e4846584d6c627a4977724a6e7a315874773256516a4e794c324f74314446465874427a305465304771672b4d716f453757436a78636e7773447076664a67504a736d373858567571637a6d6a47615a6852374e324b78567a4158326d366972396962534a77636f7964556f425761694a3238596a6c7a4d6677516f3578697477687255757a46507356654133476d632b6233465363387a3036794365356b7352613230453254597135535a754f775173586361564a737366466937784d33786b4739336e656347486e4f31474b4976555a687532546a755363365677484630497a547a66504765304e724d63584778374f37575779373978306e2f772f39534d4843726e70554b6741414141424a52553545726b4a6767673d3d', 1, 1, NULL, '#FFFFFF', '#875A7B', NULL, true, NULL, NULL, 31, 49, 28, 39, 48, 40, 29, 1, 2, NULL, 4, 27, 38, NULL, 2, NULL, 43, NULL, NULL, NULL, 1, 233, 5, NULL, NULL, NULL, 26, 32, NULL, '12', 'generic_coa', '1014', '1015', '1017', 'round_globally', 'plain', NULL, 'tax_excluded', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, true, NULL, NULL, NULL, true, NULL, NULL, false, NULL, true, 10, 17, 31, '12', 'sms', NULL, true, 365, 7, 2, 4, 3, 'manual', 'periodic', 'standard', 1, NULL, 30, NULL, NULL, NULL, true, NULL, 1, NULL, 0, NULL);

INSERT INTO public.res_country VALUES
	(104, NULL, 20, 91, 1, 1, 'IN', 'before', '{"en_US": "India"}', '{"en_US": "GSTIN"}', '%(street)s
%(street2)s
%(city)s %(zip)s
%(state_name)s %(state_code)s
%(country_name)s', true, true, '2026-11-25 07:58:14.610285', '2026-11-25 07:58:14.610285'),
	(233, NULL, 1, 1, 1, 1, 'US', 'before', '{"en_US": "United States"}', '{"en_US": ""}', '%(street)s
%(street2)s
%(city)s %(state_code)s %(zip)s
%(country_name)s', true, true, '2026-11-25 07:58:14.610285', '2026-11-25 07:58:14.610285');

INSERT INTO public.res_currency VALUES
	(1, 'USD', '$', 840, 2, NULL, 1, 'United States dollar', 'before', '{"en_US": "Dollars"}', '{"en_US": "Cents"}', 0.010000, true, NULL, '2026-11-25 07:58:14.610285'),
	(20, 'INR', '₹', 356, 2, 1, 1, 'Indian rupee', 'before', '{"en_US": "Rupees"}', '{"en_US": "Paise"}', 0.010000, false, '2026-11-25 07:58:14.610285', '2026-11-25 07:58:14.610285');

INSERT INTO public.res_partner VALUES
	(2, 1, '2026-11-25 07:58:14.610285', 'OdooBot', NULL, NULL, NULL, NULL, NULL, 0, 2, 1, 1, 'OdooBot', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, NULL, 'odoobot@example.com', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, false, '2026-11-25 07:59:14.017731', 0, 'odoobot@example.com', NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(3, 1, '2026-11-25 07:58:14.610285', 'Administrator', NULL, NULL, NULL, NULL, NULL, 0, 3, 1, 1, 'Administrator', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, NULL, false, false, '2026-11-25 07:59:14.017731', 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(1, NULL, '2026-11-25 07:58:14.610285', 'My Company', NULL, NULL, NULL, 233, NULL, 0, 1, NULL, 1, 'My Company', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', '', NULL, '', '', NULL, '', 'My Company', NULL, NULL, NULL, NULL, NULL, NULL, true, NULL, true, true, '2026-11-25 07:59:36.995365', 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '{"1": 10}', '{"1": 10}', NULL, NULL, NULL, NULL, NULL),
	(8, NULL, '2026-11-25 07:59:56.950673', 'Fixture Open Guest', NULL, NULL, NULL, 104, NULL, 0, 8, 1, 1, 'Fixture Open Guest', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, 'Ahmedabad', 'open.guest@example.com', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, NULL, false, true, '2026-11-25 07:59:56.950673', 0, 'open.guest@example.com', NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(7, NULL, '2026-11-25 07:59:56.950673', 'Fixture Invoiced Guest', NULL, NULL, NULL, 104, NULL, 0, 7, 1, 1, 'Fixture Invoiced Guest', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, 'Ahmedabad', 'invoiced.guest@example.com', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, NULL, false, true, '2026-11-25 07:59:56.950673', 0, 'invoiced.guest@example.com', NULL, NULL, NULL, NULL, 0, 1, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(4, NULL, '2026-11-25 07:58:14.610285', 'Public user', NULL, NULL, NULL, NULL, NULL, 0, 4, 1, 1, 'Public user', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, true, '2026-11-25 07:58:42.116585', 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(5, NULL, '2026-11-25 07:58:14.610285', 'Portal User Template', NULL, NULL, NULL, NULL, NULL, 0, 5, 1, 1, 'Portal User Template', NULL, 'en_US', NULL, NULL, NULL, NULL, NULL, 'contact', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, false, true, '2026-11-25 07:58:42.116585', 0, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ask', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO public.res_users VALUES
	(3, 1, 4, false, '2026-11-25 07:58:14.610285', 'public', NULL, NULL, 1, 1, '<div>Public user</div>', true, '2026-11-25 07:58:47.635182', NULL, NULL, false, 'email', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(4, 1, 5, false, '2026-11-25 07:58:14.610285', 'portaltemplate', NULL, NULL, 1, 1, '', true, '2026-11-25 07:58:47.635182', NULL, NULL, false, 'email', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
	(1, 1, 2, false, '2026-11-25 07:58:14.610285', '__system__', NULL, NULL, NULL, 1, '<div>System</div>', false, '2026-11-25 07:58:47.635182', NULL, NULL, true, 'inbox', NULL, NULL, NULL, NULL, 'disabled', NULL, NULL, NULL),
	(2, 1, 3, true, '2026-11-25 07:58:14.610285', 'admin', NULL, NULL, 1, 1, '<div>Administrator</div>', false, '2026-11-25 07:58:47.635182', NULL, NULL, true, 'email', NULL, NULL, NULL, NULL, NULL, NULL, 1, NULL);

INSERT INTO public.sale_order VALUES
	(2, NULL, NULL, NULL, 1, 7, NULL, NULL, 7, 7, 2, NULL, NULL, 2, 1, 1, 1, 1, 1, NULL, 'S00002', 'sale', NULL, NULL, NULL, NULL, 'invoiced', '2026-12-25', NULL, 1.0, 230.00, 27.60, 257.60, false, true, false, '2026-11-25 07:59:56.950673', NULL, '2026-11-25 07:59:57', NULL, '2026-11-25 07:59:56.950673', 1, NULL, NULL, 1, NULL, 'direct', NULL, NULL, NULL, NULL),
	(3, NULL, NULL, NULL, 1, 8, NULL, NULL, 8, 8, 2, NULL, NULL, 2, 1, 1, 1, 1, 1, NULL, 'S00003', 'sale', NULL, NULL, NULL, NULL, 'to invoice', '2026-12-25', NULL, 1.0, 310.00, 37.20, 347.20, false, true, false, '2026-11-25 07:59:56.950673', NULL, '2026-11-25 07:59:57', NULL, '2026-11-25 07:59:56.950673', 1, NULL, NULL, 1, NULL, 'direct', NULL, NULL, NULL, NULL);

INSERT INTO public.sale_order_line VALUES
	(2, 2, 10, 1, 1, 7, 1, 7, 1, NULL, NULL, 1, 1, 'sale', NULL, NULL, NULL, 'stock_move', 'invoiced', NULL, NULL, 'FX-101', 2.00, 100.0, 0.00, 200.00, 224.00, 100.00, 112.00, 0.00, 2.00, 0.00, 200.00, 0.00, NULL, NULL, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 100, 24, 0, false, 1, false, NULL, NULL),
	(3, 2, 10, 1, 1, 7, 1, 6, 1, NULL, NULL, 1, 1, 'sale', NULL, NULL, NULL, 'stock_move', 'invoiced', NULL, NULL, 'Fixture Breakfast', 2.00, 15.0, 0.00, 30.00, 33.60, 15.00, 16.80, 0.00, 2.00, 0.00, 30.00, 0.00, NULL, NULL, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 15, 3.6000000000000014, 0, false, 1, false, NULL, NULL),
	(4, 3, 10, 1, 1, 8, 1, 8, 1, NULL, NULL, 1, 1, 'sale', NULL, NULL, NULL, 'stock_move', 'to invoice', NULL, NULL, 'FX-102', 2.00, 140.0, 0.00, 280.00, 313.60, 140.00, 156.80, 0.00, 0.00, 2.00, 0.00, 280.00, NULL, NULL, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 140, 33.60000000000002, 0, false, 1, false, NULL, NULL),
	(5, 3, 10, 1, 1, 8, 1, 6, 1, NULL, NULL, 1, 1, 'sale', NULL, NULL, NULL, 'stock_move', 'to invoice', NULL, NULL, 'Fixture Breakfast', 2.00, 15.0, 0.00, 30.00, 33.60, 15.00, 16.80, 0.00, 0.00, 2.00, 0.00, 30.00, NULL, NULL, false, false, '2026-11-25 07:59:56.950673', '2026-11-25 07:59:56.950673', 15, 3.6000000000000014, 0, false, 1, false, NULL, NULL);

INSERT INTO public.sale_order_line_invoice_rel VALUES
	(1, 2),
	(2, 3);

INSERT INTO public.stock_warehouse VALUES
	(1, 1, 1, 4, 5, 6, 7, 8, 9, 3, 3, 4, 2, 1, 7, 5, 6, 8, 2, 3, 10, 1, 1, 'My Company', 'WH', 'one_step', 'ship_only', true, '2026-11-25 07:59:14.017731', '2026-11-25 07:59:14.017731');

INSERT INTO public.uom_uom VALUES
	(1, 100, NULL, 1, 1, '1/', '{"en_US": "Units"}', 1.0, 1.0, true, '2026-11-25 07:58:27.704706', '2026-11-25 07:58:27.704706', NULL);

SELECT pg_catalog.setval('public.account_move_id_seq', 1, true);

SELECT pg_catalog.setval('public.account_move_line_id_seq', 4, true);

SELECT pg_catalog.setval('public.account_tax_id_seq', 6, true);

SELECT pg_catalog.setval('public.folio_room_line_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_floor_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_folio_id_seq', 3, true);

SELECT pg_catalog.setval('public.hotel_folio_line_id_seq', 3, true);

SELECT pg_catalog.setval('public.hotel_room_amenities_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_room_amenities_type_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_room_id_seq', 4, true);

SELECT pg_catalog.setval('public.hotel_room_type_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_service_line_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_service_type_id_seq', 2, true);

SELECT pg_catalog.setval('public.hotel_services_id_seq', 2, true);

SELECT pg_catalog.setval('public.ir_attachment_id_seq', 517, true);

SELECT pg_catalog.setval('public.ir_config_parameter_id_seq', 23, true);

SELECT pg_catalog.setval('public.ir_module_module_id_seq', 684, true);

SELECT pg_catalog.setval('public.product_category_id_seq', 9, true);

SELECT pg_catalog.setval('public.product_pricelist_id_seq', 2, true);

SELECT pg_catalog.setval('public.product_product_id_seq', 8, true);

SELECT pg_catalog.setval('public.product_template_id_seq', 8, true);

SELECT pg_catalog.setval('public.res_company_id_seq', 1, true);

SELECT pg_catalog.setval('public.res_country_id_seq', 251, true);

SELECT pg_catalog.setval('public.res_country_state_id_seq', 2131, true);

SELECT pg_catalog.setval('public.res_currency_id_seq', 170, true);

SELECT pg_catalog.setval('public.res_partner_id_seq', 8, true);

SELECT pg_catalog.setval('public.res_users_id_seq', 4, true);

SELECT pg_catalog.setval('public.sale_order_id_seq', 3, true);

SELECT pg_catalog.setval('public.sale_order_line_id_seq', 5, true);

SELECT pg_catalog.setval('public.stock_warehouse_id_seq', 1, true);

SELECT pg_catalog.setval('public.uom_uom_id_seq', 30, true);
